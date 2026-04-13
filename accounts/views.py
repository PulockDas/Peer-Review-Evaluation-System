from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils import timezone
from django.views.generic import TemplateView

from .mixins import RoleRequiredMixin
from .models import User


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"


class DashboardRedirectView(LoginRequiredMixin, TemplateView):
    """Redirect each user to their role-specific dashboard."""

    def get(self, request, *args, **kwargs):
        role = getattr(request.user, "role", User.Roles.STUDENT)
        if role == User.Roles.ADMIN:
            return redirect("accounts:dashboard_admin")
        if role == User.Roles.INSTRUCTOR:
            return redirect("accounts:dashboard_instructor")
        return redirect("accounts:dashboard_student")


class AdminDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = (User.Roles.ADMIN,)
    template_name = "accounts/dashboard_admin.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        from courses.models import Course
        from grading.models import FinalGrade
        from reviews.models import ReviewAssignment
        from submissions.models import Submission

        ctx["total_users"] = User.objects.count()
        ctx["total_instructors"] = User.objects.filter(role=User.Roles.INSTRUCTOR).count()
        ctx["total_students"] = User.objects.filter(role=User.Roles.STUDENT).count()
        ctx["total_courses"] = Course.objects.count()
        ctx["total_submissions"] = Submission.objects.count()
        ctx["pending_reviews"] = ReviewAssignment.objects.filter(
            review_status=ReviewAssignment.Status.PENDING
        ).count()
        ctx["released_grades"] = FinalGrade.objects.filter(
            grade_status=FinalGrade.Status.RELEASED
        ).count()
        ctx["recent_users"] = (
            User.objects.select_related()
            .order_by("-date_joined")[:8]
        )
        return ctx


class InstructorDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = (User.Roles.INSTRUCTOR,)
    template_name = "accounts/dashboard_instructor.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        from assignments.models import Assignment
        from courses.models import Course
        from grading.models import FinalGrade
        from reviews.models import ReviewAssignment
        from submissions.models import Submission

        instructor = self.request.user
        course_pks = list(
            Course.objects.filter(instructor=instructor).values_list("pk", flat=True)
        )
        assignment_pks = list(
            Assignment.objects.filter(course__pk__in=course_pks).values_list("pk", flat=True)
        )
        now = timezone.now()

        ctx["course_count"] = len(course_pks)
        ctx["assignment_count"] = len(assignment_pks)
        ctx["submission_count"] = Submission.objects.filter(
            assignment__pk__in=assignment_pks
        ).count()
        ctx["pending_reviews"] = ReviewAssignment.objects.filter(
            submission__assignment__pk__in=assignment_pks,
            review_status=ReviewAssignment.Status.PENDING,
        ).count()
        ctx["released_grades"] = FinalGrade.objects.filter(
            submission__assignment__pk__in=assignment_pks,
            grade_status=FinalGrade.Status.RELEASED,
        ).count()
        ctx["upcoming_deadlines"] = (
            Assignment.objects.filter(
                pk__in=assignment_pks,
                due_date__gte=now,
                due_date__lte=now + timedelta(days=7),
            )
            .select_related("course")
            .order_by("due_date")
        )
        return ctx


class StudentDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = (User.Roles.STUDENT,)
    template_name = "accounts/dashboard_student.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        from assignments.models import Assignment
        from courses.models import Enrollment
        from grading.models import FinalGrade
        from reviews.models import ReviewAssignment

        student = self.request.user
        enrolled_course_pks = list(
            Enrollment.objects.filter(student=student).values_list("course_id", flat=True)
        )
        now = timezone.now()

        ctx["enrolled_count"] = len(enrolled_course_pks)
        ctx["pending_reviews"] = ReviewAssignment.objects.filter(
            reviewer=student,
            review_status__in=[
                ReviewAssignment.Status.PENDING,
                ReviewAssignment.Status.IN_PROGRESS,
            ],
        ).count()
        ctx["released_grades"] = FinalGrade.objects.filter(
            submission__student=student,
            grade_status=FinalGrade.Status.RELEASED,
        ).count()
        ctx["upcoming_assignments"] = (
            Assignment.objects.filter(
                course__pk__in=enrolled_course_pks,
                due_date__gte=now,
            )
            .select_related("course")
            .order_by("due_date")[:5]
        )
        return ctx
