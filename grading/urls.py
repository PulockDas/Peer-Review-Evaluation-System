from django.urls import path

from .views import GradingDashboardView

app_name = "grading"

urlpatterns = [
    path("dashboard/", GradingDashboardView.as_view(), name="dashboard"),
]

