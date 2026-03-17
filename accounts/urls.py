from django.urls import path
from django.contrib.auth.views import LoginView, LogoutView

from . import views

app_name = "accounts"

urlpatterns = [
    path(
        "login/",
        LoginView.as_view(
            template_name="accounts/login.html",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("dashboard/", views.DashboardRedirectView.as_view(), name="dashboard"),
    path("dashboard/admin/", views.AdminDashboardView.as_view(), name="dashboard_admin"),
    path(
        "dashboard/instructor/",
        views.InstructorDashboardView.as_view(),
        name="dashboard_instructor",
    ),
    path("dashboard/student/", views.StudentDashboardView.as_view(), name="dashboard_student"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
]

