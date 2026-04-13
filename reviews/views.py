from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, ListView, TemplateView, View

from accounts.mixins import RoleRequiredMixin
from accounts.models import User
from assignments.models import Assignment

from .forms import CriterionScoreForm, ReviewForm
from .models import Review, ReviewAssignment, ReviewCriterionScore
from .services import AllocationError, allocate_reviewers, delete_allocations


# ---------------------------------------------------------------------------
# Student: list of assigned reviews
# ---------------------------------------------------------------------------

class MyReviewsListView(RoleRequiredMixin, ListView):
    """Show the current student all review assignments they have been given."""

    allowed_roles = (User.Roles.STUDENT,)
    template_name = "reviews/my_reviews.html"
    context_object_name = "review_assignments"

    def get_queryset(self):
        return (
            ReviewAssignment.objects.filter(reviewer=self.request.user)
            .select_related("submission__assignment__course")
            .prefetch_related("review")
            .order_by("-assigned_at")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        # Annotate each RA with whether a Review exists
        for ra in ctx["review_assignments"]:
            try:
                ra.submitted_review = ra.review
            except Review.DoesNotExist:
                ra.submitted_review = None
        return ctx


# ---------------------------------------------------------------------------
# Student: review form (anonymous token access)
# ---------------------------------------------------------------------------

class ReviewFormView(RoleRequiredMixin, View):
    """
    Reviewer opens this page to score a submission.

    Access is via the ReviewAssignment's anonymous_token, so neither the URL
    nor the page content reveals the author's identity.
    """

    allowed_roles = (User.Roles.STUDENT,)
    template_name = "reviews/review_form.html"

    # --- setup --------------------------------------------------------------

    def dispatch(self, request, *args, **kwargs):
        self.ra = (
            ReviewAssignment.objects.filter(anonymous_token=kwargs["token"])
            .select_related(
                "submission__assignment__course",
                "reviewer",
            )
            .first()
        )
        if not self.ra:
            raise Http404

        # Only the assigned reviewer may open this page
        if self.ra.reviewer_id != request.user.pk:
            raise Http404

        # Existing review (read-only mode if present)
        try:
            self.existing_review = self.ra.review
        except Review.DoesNotExist:
            self.existing_review = None

        # Rubric + criteria (may be absent)
        try:
            self.rubric = self.ra.submission.assignment.rubric
            self.criteria = list(self.rubric.criteria.all())
        except Exception:
            self.rubric = None
            self.criteria = []

        return super().dispatch(request, *args, **kwargs)

    # --- GET ----------------------------------------------------------------

    def get(self, request, *args, **kwargs):
        review_form = ReviewForm(instance=self.existing_review)
        criterion_forms = self._build_criterion_forms()
        return render(request, self.template_name, self._ctx(review_form, criterion_forms))

    # --- POST ---------------------------------------------------------------

    def post(self, request, *args, **kwargs):
        if self.existing_review:
            messages.warning(request, "You have already submitted this review.")
            return redirect("reviews:my_reviews")

        review_form = ReviewForm(request.POST)
        criterion_forms = self._build_criterion_forms(request.POST)

        all_valid = review_form.is_valid()
        for form in criterion_forms.values():
            if not form.is_valid():
                all_valid = False

        if all_valid:
            review = review_form.save(commit=False)
            review.review_assignment = self.ra

            # Compute total score from criteria
            total = Decimal("0")
            for form in criterion_forms.values():
                total += form.cleaned_data["score"]
            review.total_score = total
            review.save()

            # Persist criterion scores
            for criterion, form in criterion_forms.items():
                ReviewCriterionScore.objects.create(
                    review=review,
                    criterion=criterion,
                    score=form.cleaned_data["score"],
                    comment=form.cleaned_data.get("comment", ""),
                )

            # Mark assignment complete
            self.ra.review_status = ReviewAssignment.Status.COMPLETED
            self.ra.save()

            messages.success(request, "Your review has been submitted successfully.")
            return redirect("reviews:my_reviews")

        return render(request, self.template_name, self._ctx(review_form, criterion_forms))

    # --- helpers ------------------------------------------------------------

    def _build_criterion_forms(self, data=None):
        forms = {}
        for criterion in self.criteria:
            prefix = f"criterion_{criterion.pk}"
            initial = {}
            if self.existing_review:
                try:
                    cs = self.existing_review.criterion_scores.get(criterion=criterion)
                    initial = {"score": cs.score, "comment": cs.comment}
                except ReviewCriterionScore.DoesNotExist:
                    pass
            if data is not None:
                forms[criterion] = CriterionScoreForm(
                    data, prefix=prefix, max_marks=criterion.max_marks
                )
            else:
                forms[criterion] = CriterionScoreForm(
                    prefix=prefix, initial=initial, max_marks=criterion.max_marks
                )
        return forms

    def _ctx(self, review_form, criterion_forms):
        criterion_data = []
        for criterion, form in criterion_forms.items():
            existing_score = None
            if self.existing_review:
                try:
                    existing_score = self.existing_review.criterion_scores.get(
                        criterion=criterion
                    )
                except ReviewCriterionScore.DoesNotExist:
                    pass
            criterion_data.append(
                {
                    "criterion": criterion,
                    "form": form,
                    "existing_score": existing_score,
                }
            )
        return {
            "ra": self.ra,
            "assignment": self.ra.submission.assignment,
            "submission": self.ra.submission,
            "rubric": self.rubric,
            "existing_review": self.existing_review,
            "review_form": review_form,
            "criterion_data": criterion_data,
            "is_submitted": self.existing_review is not None,
        }


# ---------------------------------------------------------------------------
# Instructor: review completion monitor
# ---------------------------------------------------------------------------

class InstructorMonitorView(RoleRequiredMixin, TemplateView):
    """Instructor sees review completion progress for a given assignment."""

    allowed_roles = (User.Roles.INSTRUCTOR,)
    template_name = "reviews/instructor_monitor.html"

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

        ras = (
            ReviewAssignment.objects.filter(submission__assignment=self.assignment)
            .select_related("submission__student", "reviewer")
            .prefetch_related("review")
            .order_by(
                "submission__student__last_name",
                "submission__student__first_name",
                "reviewer__last_name",
            )
        )

        grouped: dict = defaultdict(list)
        for ra in ras:
            try:
                ra.submitted_review = ra.review
            except Review.DoesNotExist:
                ra.submitted_review = None
            grouped[ra.submission].append(ra)

        ctx["grouped"] = sorted(
            grouped.items(),
            key=lambda item: (
                item[0].student.last_name,
                item[0].student.first_name,
            ),
        )
        ctx["total"] = ras.count()
        ctx["completed"] = ras.filter(review_status=ReviewAssignment.Status.COMPLETED).count()
        ctx["pending"] = ras.filter(review_status=ReviewAssignment.Status.PENDING).count()
        ctx["in_progress"] = ras.filter(
            review_status=ReviewAssignment.Status.IN_PROGRESS
        ).count()
        return ctx


# ---------------------------------------------------------------------------
# Instructor: view a single submitted review in full
# ---------------------------------------------------------------------------

class InstructorReviewDetailView(RoleRequiredMixin, DetailView):
    """Instructor reads one submitted peer review including all criterion scores."""

    allowed_roles = (User.Roles.INSTRUCTOR,)
    model = Review
    template_name = "reviews/instructor_review_detail.html"
    pk_url_kwarg = "review_id"

    def get_queryset(self):
        return (
            Review.objects.filter(
                review_assignment__submission__assignment__course__instructor=self.request.user
            )
            .select_related(
                "review_assignment__submission__student",
                "review_assignment__submission__assignment__course",
                "review_assignment__reviewer",
            )
            .prefetch_related("criterion_scores__criterion")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["assignment"] = self.object.review_assignment.submission.assignment
        ctx["criterion_scores"] = self.object.criterion_scores.select_related(
            "criterion"
        ).order_by("criterion__order", "criterion__pk")
        return ctx


# ---------------------------------------------------------------------------
# Instructor: reviewer allocation management (existing)
# ---------------------------------------------------------------------------

class AllocationView(RoleRequiredMixin, TemplateView):
    """Instructor manages reviewer allocation for one assignment."""

    allowed_roles = (User.Roles.INSTRUCTOR,)
    template_name = "reviews/allocation.html"

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

        review_assignments = (
            ReviewAssignment.objects.filter(submission__assignment=self.assignment)
            .select_related("submission__student", "reviewer")
            .order_by(
                "submission__student__last_name",
                "submission__student__first_name",
                "reviewer__last_name",
            )
        )

        grouped: dict = defaultdict(list)
        for ra in review_assignments:
            grouped[ra.submission].append(ra)

        ctx["grouped"] = sorted(
            grouped.items(),
            key=lambda item: (
                item[0].student.last_name,
                item[0].student.first_name,
                item[0].student.username,
            ),
        )
        ctx["allocation_exists"] = review_assignments.exists()
        ctx["total_assignments"] = review_assignments.count()
        ctx["submission_count"] = self.assignment.submissions.count()

        workload: dict = defaultdict(int)
        for ra in review_assignments:
            workload[ra.reviewer] += 1
        ctx["workload"] = sorted(
            workload.items(),
            key=lambda item: (-item[1], item[0].last_name),
        )
        return ctx

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action", "")

        if action == "allocate":
            already_exists = ReviewAssignment.objects.filter(
                submission__assignment=self.assignment
            ).exists()
            if already_exists:
                messages.warning(
                    request,
                    'Allocation already exists. Use "Reset & re-allocate" to redo it.',
                )
                return redirect("reviews:allocate", assignment_id=self.assignment.pk)
            self._run_allocation(request)

        elif action == "reset":
            deleted = delete_allocations(self.assignment)
            if deleted:
                messages.info(request, f"Removed {deleted} existing review assignments.")
            self._run_allocation(request)

        else:
            messages.error(request, "Unknown action.")

        return redirect("reviews:allocate", assignment_id=self.assignment.pk)

    def _run_allocation(self, request):
        try:
            created = allocate_reviewers(self.assignment)
            messages.success(
                request,
                f"Successfully created {len(created)} review assignment(s) "
                f"({len(created) // max(self.assignment.submissions.count(), 1)} per submission).",
            )
        except AllocationError as exc:
            messages.error(request, str(exc))
