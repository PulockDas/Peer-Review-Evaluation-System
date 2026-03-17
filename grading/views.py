from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class GradingDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "grading/dashboard.html"

