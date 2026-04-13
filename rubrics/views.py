from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView

from accounts.mixins import RoleRequiredMixin
from accounts.models import User
from assignments.models import Assignment
from courses.models import Enrollment

from .forms import RubricCriterionForm, RubricForm
from .models import Rubric, RubricCriterion


# ---------------------------------------------------------------------------
# Shared access helper
# ---------------------------------------------------------------------------

def _get_assignment_or_404(assignment_id, request):
    """
    Return the Assignment for the given pk after checking role-based access.
    Also returns a boolean indicating whether the user can manage the rubric.
    """
    assignment = (
        Assignment.objects.filter(pk=assignment_id)
        .select_related("course")
        .first()
    )
    if not assignment:
        raise Http404

    role = getattr(request.user, "role", None)

    if role == User.Roles.INSTRUCTOR:
        if assignment.course.instructor_id != request.user.id:
            raise Http404
        return assignment, True

    if role == User.Roles.STUDENT:
        if not Enrollment.objects.filter(
            course=assignment.course, student=request.user
        ).exists():
            raise Http404
        return assignment, False

    raise Http404


# ---------------------------------------------------------------------------
# Rubric detail / landing page  (both instructor & student)
# ---------------------------------------------------------------------------

class RubricDetailView(LoginRequiredMixin, TemplateView):
    template_name = "rubrics/rubric_detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.assignment, self.can_manage = _get_assignment_or_404(
            kwargs["assignment_id"], request
        )
        try:
            self.rubric = self.assignment.rubric
        except Rubric.DoesNotExist:
            self.rubric = None

        # Instructor with no rubric yet → go straight to create
        if self.rubric is None and self.can_manage:
            return redirect("rubrics:create", assignment_id=self.assignment.pk)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["assignment"] = self.assignment
        ctx["rubric"] = self.rubric
        ctx["can_manage"] = self.can_manage
        if self.rubric:
            criteria = list(self.rubric.criteria.all())
            ctx["criteria"] = criteria
            ctx["total_max_marks"] = sum(c.max_marks for c in criteria)
            ctx["total_weight"] = sum(c.weight for c in criteria)
        return ctx


# ---------------------------------------------------------------------------
# Rubric create  (instructor only)
# ---------------------------------------------------------------------------

class RubricCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Roles.INSTRUCTOR,)
    model = Rubric
    form_class = RubricForm
    template_name = "rubrics/rubric_form.html"

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

        # Rubric already exists → redirect to detail
        if hasattr(self.assignment, "rubric"):
            return redirect("rubrics:detail", assignment_id=self.assignment.pk)

        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.assignment = self.assignment
        messages.success(self.request, "Rubric created. Now add criteria below.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("rubrics:detail", kwargs={"assignment_id": self.assignment.pk})

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["assignment"] = self.assignment
        return ctx


# ---------------------------------------------------------------------------
# Criterion add  (instructor only)
# ---------------------------------------------------------------------------

class CriterionCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Roles.INSTRUCTOR,)
    model = RubricCriterion
    form_class = RubricCriterionForm
    template_name = "rubrics/criterion_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.rubric = get_object_or_404(
            Rubric,
            pk=kwargs["rubric_id"],
            assignment__course__instructor=request.user,
        )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.rubric = self.rubric
        messages.success(self.request, "Criterion added.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "rubrics:detail",
            kwargs={"assignment_id": self.rubric.assignment_id},
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rubric"] = self.rubric
        ctx["editing"] = False
        return ctx


# ---------------------------------------------------------------------------
# Criterion edit  (instructor only)
# ---------------------------------------------------------------------------

class CriterionUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = (User.Roles.INSTRUCTOR,)
    model = RubricCriterion
    form_class = RubricCriterionForm
    template_name = "rubrics/criterion_form.html"
    pk_url_kwarg = "criterion_id"

    def get_queryset(self):
        return RubricCriterion.objects.filter(
            rubric__assignment__course__instructor=self.request.user
        )

    def form_valid(self, form):
        messages.success(self.request, "Criterion updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "rubrics:detail",
            kwargs={"assignment_id": self.object.rubric.assignment_id},
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["rubric"] = self.object.rubric
        ctx["editing"] = True
        return ctx


# ---------------------------------------------------------------------------
# Criterion delete  (instructor only)
# ---------------------------------------------------------------------------

class CriterionDeleteView(RoleRequiredMixin, DeleteView):
    allowed_roles = (User.Roles.INSTRUCTOR,)
    model = RubricCriterion
    template_name = "rubrics/criterion_confirm_delete.html"
    pk_url_kwarg = "criterion_id"

    def get_queryset(self):
        return RubricCriterion.objects.filter(
            rubric__assignment__course__instructor=self.request.user
        )

    def form_valid(self, form):
        messages.success(self.request, "Criterion removed.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            "rubrics:detail",
            kwargs={"assignment_id": self.object.rubric.assignment_id},
        )
