from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, QuerySet
from django.http import Http404
from django.urls import reverse
from django.views.generic import CreateView, ListView

from accounts.mixins import RoleRequiredMixin
from accounts.models import User
from courses.models import Course, Enrollment

from .forms import AssignmentForm
from .models import Assignment


class CourseAssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    template_name = "assignments/assignment_list.html"
    context_object_name = "assignments"

    def dispatch(self, request, *args, **kwargs):
        self.course = Course.objects.filter(pk=kwargs["course_id"]).first()
        if not self.course:
            raise Http404

        role = getattr(request.user, "role", None)
        if role == User.Roles.INSTRUCTOR and self.course.instructor_id != request.user.id:
            raise Http404
        if role == User.Roles.STUDENT and not Enrollment.objects.filter(
            course=self.course, student=request.user
        ).exists():
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self) -> QuerySet[Assignment]:
        qs = Assignment.objects.filter(course=self.course).order_by("due_date")
        if getattr(self.request.user, "role", None) == User.Roles.INSTRUCTOR:
            qs = qs.annotate(submission_count=Count("submissions"))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["course"] = self.course
        role = getattr(self.request.user, "role", None)
        ctx["can_manage"] = role == User.Roles.INSTRUCTOR and (
            self.course.instructor_id == self.request.user.id
        )

        # Build a set of assignment IDs that already have a rubric
        from rubrics.models import Rubric

        rubric_ids = set(
            Rubric.objects.filter(assignment__course=self.course)
            .values_list("assignment_id", flat=True)
        )

        if role == User.Roles.STUDENT:
            from submissions.models import Submission

            sub_map = {
                s.assignment_id: s
                for s in Submission.objects.filter(
                    assignment__course=self.course,
                    student=self.request.user,
                )
            }
            assignments = list(ctx["assignments"])
            for a in assignments:
                a.my_submission = sub_map.get(a.pk)
                a.has_rubric = a.pk in rubric_ids
            ctx["assignments"] = assignments

        else:
            # Instructor path: just annotate has_rubric
            assignments = list(ctx["assignments"])
            for a in assignments:
                a.has_rubric = a.pk in rubric_ids
            ctx["assignments"] = assignments

        return ctx


class AssignmentCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Roles.INSTRUCTOR,)
    model = Assignment
    form_class = AssignmentForm
    template_name = "assignments/assignment_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.course = Course.objects.filter(pk=kwargs["course_id"], instructor=request.user).first()
        if not self.course:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.course = self.course
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("assignments:list", kwargs={"course_id": self.course.pk})
