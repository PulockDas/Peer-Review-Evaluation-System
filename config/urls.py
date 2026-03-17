from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("courses/", include(("courses.urls", "courses"), namespace="courses")),
    path("assignments/", include(("assignments.urls", "assignments"), namespace="assignments")),
    path(
        "",
        TemplateView.as_view(template_name="home.html"),
        name="home",
    ),
]

