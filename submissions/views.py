import os

from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from django.utils import timezone
from django.views.generic import FormView, ListView

from accounts.mixins import RoleRequiredMixin
from accounts.models import User
from assignments.models import Assignment
from courses.models import Enrollment

from .forms import SubmissionForm
from .models import Submission


class StudentSubmitView(RoleRequiredMixin, FormView):
    """Student creates or replaces their submission for an assignment."""

    allowed_roles = (User.Roles.STUDENT,)
    template_name = "submissions/submission_form.html"
    form_class = SubmissionForm

    def dispatch(self, request, *args, **kwargs):
        self.assignment = (
            Assignment.objects.filter(pk=kwargs["assignment_id"])
            .select_related("course")
            .first()
        )
        if not self.assignment:
            raise Http404

        if not Enrollment.objects.filter(
            course=self.assignment.course, student=request.user
        ).exists():
            raise Http404

        self.existing = Submission.objects.filter(
            assignment=self.assignment, student=request.user
        ).first()

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.existing
        return kwargs

    def form_valid(self, form):
        submission = form.save(commit=False)
        submission.assignment = self.assignment
        submission.student = self.request.user
        submission.status = (
            Submission.Status.LATE
            if timezone.now() > self.assignment.due_date
            else Submission.Status.SUBMITTED
        )
        submission.save()

        verb = "updated" if self.existing else "submitted"
        messages.success(self.request, f"Submission {verb} successfully.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "assignments:list",
            kwargs={"course_id": self.assignment.course_id},
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["assignment"] = self.assignment
        ctx["existing"] = self.existing
        ctx["is_past_due"] = timezone.now() > self.assignment.due_date
        if self.existing and self.existing.file:
            ctx["existing_filename"] = os.path.basename(self.existing.file.name)
        return ctx


class InstructorSubmissionListView(RoleRequiredMixin, ListView):
    """Instructor views all submissions for a given assignment."""

    allowed_roles = (User.Roles.INSTRUCTOR,)
    template_name = "submissions/instructor_submission_list.html"
    context_object_name = "submissions"

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

    def get_queryset(self):
        return (
            Submission.objects.filter(assignment=self.assignment)
            .select_related("student")
            .order_by("student__last_name", "student__first_name")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["assignment"] = self.assignment
        enrolled_count = Enrollment.objects.filter(
            course=self.assignment.course
        ).count()
        ctx["enrolled_count"] = enrolled_count
        submitted_count = self.get_queryset().count()
        ctx["submitted_count"] = submitted_count
        ctx["pending_count"] = max(enrolled_count - submitted_count, 0)
        return ctx
