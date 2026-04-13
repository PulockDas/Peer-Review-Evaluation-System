from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import User
from assignments.models import Assignment
from submissions.models import Submission

from .models import FinalGrade, ReviewerAccuracy
from .services import GradingError, calculate_grades_for_assignment, release_grades, unrelease_grades


# ---------------------------------------------------------------------------
# Instructor: grade management for one assignment
# ---------------------------------------------------------------------------

class GradeManagementView(RoleRequiredMixin, TemplateView):
    """
    Central instructor page for an assignment's grades.

    GET  – shows each submission with its grade status, score, and letter grade.
    POST – dispatches to calculate / recalculate / release / unrelease actions.
    """

    allowed_roles = (User.Roles.INSTRUCTOR,)
    template_name = "grading/grade_management.html"

    def dispatch(self, request, *args, **kwargs):
        self.assignment = (
            Assignment.objects.filter(
                pk=kwargs["assignment_id"],
                course__instructor=request.user,
            )
            .select_related("course")
            .first()
        )
        if not self.assignment:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    # --- GET ----------------------------------------------------------------

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["assignment"] = self.assignment

        submissions = (
            Submission.objects.filter(assignment=self.assignment)
            .select_related("student")
            .prefetch_related("review_assignments", "final_grade")
            .order_by("student__last_name", "student__first_name")
        )

        rows = []
        for sub in submissions:
            completed_reviews = sum(
                1
                for ra in sub.review_assignments.all()
                if ra.review_status == "COMPLETED"
            )
            try:
                grade = sub.final_grade
            except FinalGrade.DoesNotExist:
                grade = None

            rows.append(
                {
                    "submission": sub,
                    "completed_reviews": completed_reviews,
                    "grade": grade,
                    "ready": completed_reviews >= 3,
                }
            )

        ctx["rows"] = rows
        ctx["total_submissions"] = len(rows)
        ctx["calculated_count"] = sum(1 for r in rows if r["grade"])
        ctx["released_count"] = sum(
            1
            for r in rows
            if r["grade"] and r["grade"].grade_status == FinalGrade.Status.RELEASED
        )
        ctx["has_calculated_only"] = any(
            r["grade"] and r["grade"].grade_status == FinalGrade.Status.CALCULATED
            for r in rows
        )
        ctx["has_released"] = ctx["released_count"] > 0
        return ctx

    # --- POST ---------------------------------------------------------------

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "")

        if action == "calculate":
            self._do_calculate(request, force=False)
        elif action == "recalculate":
            self._do_calculate(request, force=True)
        elif action == "release":
            n = release_grades(self.assignment)
            messages.success(request, f"Released {n} grade(s) to students.")
        elif action == "unrelease":
            n = unrelease_grades(self.assignment)
            messages.info(request, f"Un-released {n} grade(s) (reverted to Calculated).")
        else:
            messages.error(request, "Unknown action.")

        return redirect("grading:manage", assignment_id=self.assignment.pk)

    def _do_calculate(self, request, force: bool):
        try:
            n_calc, n_skip = calculate_grades_for_assignment(self.assignment, force=force)
            messages.success(
                request,
                f"Calculated {n_calc} grade(s). Skipped {n_skip} "
                f"(insufficient reviews or already released).",
            )
        except GradingError as exc:
            messages.error(request, str(exc))


# ---------------------------------------------------------------------------
# Instructor: reviewer accuracy statistics
# ---------------------------------------------------------------------------

class ReviewerAccuracyView(RoleRequiredMixin, TemplateView):
    """Shows per-reviewer accuracy statistics for a given assignment."""

    allowed_roles = (User.Roles.INSTRUCTOR,)
    template_name = "grading/reviewer_accuracy.html"

    def dispatch(self, request, *args, **kwargs):
        self.assignment = (
            Assignment.objects.filter(
                pk=kwargs["assignment_id"],
                course__instructor=request.user,
            )
            .select_related("course")
            .first()
        )
        if not self.assignment:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["assignment"] = self.assignment

        accuracies = (
            ReviewerAccuracy.objects.filter(submission__assignment=self.assignment)
            .select_related(
                "reviewer",
                "submission__student",
                "review__review_assignment",
            )
            .order_by("reviewer__last_name", "reviewer__first_name", "-accuracy_score")
        )
        ctx["accuracies"] = accuracies

        # Per-reviewer summary (avg accuracy + avg deviation)
        reviewer_agg: dict = defaultdict(
            lambda: {"count": 0, "sum_accuracy": Decimal(0), "sum_deviation": Decimal(0)}
        )
        for acc in accuracies:
            d = reviewer_agg[acc.reviewer]
            d["count"] += 1
            d["sum_accuracy"] += acc.accuracy_score
            d["sum_deviation"] += acc.deviation_from_average

        summary = []
        for reviewer, d in reviewer_agg.items():
            n = d["count"]
            summary.append(
                {
                    "reviewer": reviewer,
                    "review_count": n,
                    "avg_accuracy": round(d["sum_accuracy"] / n, 2),
                    "avg_deviation": round(d["sum_deviation"] / n, 2),
                }
            )
        ctx["reviewer_summary"] = sorted(summary, key=lambda x: -x["avg_accuracy"])
        return ctx


# ---------------------------------------------------------------------------
# Student: list of released grades
# ---------------------------------------------------------------------------

class StudentGradeListView(RoleRequiredMixin, ListView):
    """Show the current student all released final grades across all courses."""

    allowed_roles = (User.Roles.STUDENT,)
    template_name = "grading/student_grade_list.html"
    context_object_name = "grades"

    def get_queryset(self):
        return (
            FinalGrade.objects.filter(
                submission__student=self.request.user,
                grade_status=FinalGrade.Status.RELEASED,
            )
            .select_related("submission__assignment__course")
            .order_by("-released_at")
        )


# ---------------------------------------------------------------------------
# Student: detailed result for one submission
# ---------------------------------------------------------------------------

class StudentResultView(RoleRequiredMixin, TemplateView):
    """
    Show a student their final grade and anonymous peer feedback for one
    submission.  Only accessible after the grade has been released.
    """

    allowed_roles = (User.Roles.STUDENT,)
    template_name = "grading/student_result.html"

    def dispatch(self, request, *args, **kwargs):
        # Verify the student owns this submission
        submission = (
            Submission.objects.filter(
                pk=kwargs["submission_id"],
                student=request.user,
            )
            .select_related("assignment__course")
            .first()
        )
        if not submission:
            raise Http404

        # Verify a released grade exists
        try:
            grade = submission.final_grade
        except FinalGrade.DoesNotExist:
            raise Http404

        if grade.grade_status != FinalGrade.Status.RELEASED:
            raise Http404

        self.submission = submission
        self.grade = grade
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["submission"] = self.submission
        ctx["assignment"] = self.submission.assignment
        ctx["grade"] = self.grade

        # Anonymous peer reviews (reviewer identity hidden)
        from reviews.models import ReviewAssignment

        completed_ras = (
            ReviewAssignment.objects.filter(
                submission=self.submission,
                review_status="COMPLETED",
            )
            .prefetch_related("review__criterion_scores__criterion")
            .order_by("pk")
        )

        anon_reviews = []
        for i, ra in enumerate(completed_ras, 1):
            try:
                review = ra.review
                scores = review.criterion_scores.select_related("criterion").order_by(
                    "criterion__order", "criterion__pk"
                )
                anon_reviews.append(
                    {
                        "number": i,
                        "total_score": review.total_score,
                        "overall_comment": review.overall_comment,
                        "criterion_scores": list(scores),
                    }
                )
            except Exception:
                pass

        ctx["anon_reviews"] = anon_reviews

        # Rubric for criterion display headings
        try:
            ctx["rubric"] = self.submission.assignment.rubric
        except Exception:
            ctx["rubric"] = None

        return ctx
