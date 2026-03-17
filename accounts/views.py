from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView

from .mixins import RoleRequiredMixin
from .models import User


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"


class DashboardRedirectView(LoginRequiredMixin, TemplateView):
    """
    Redirect users to their role-based dashboard.
    """

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


class InstructorDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = (User.Roles.INSTRUCTOR,)
    template_name = "accounts/dashboard_instructor.html"


class StudentDashboardView(RoleRequiredMixin, TemplateView):
    allowed_roles = (User.Roles.STUDENT,)
    template_name = "accounts/dashboard_student.html"

