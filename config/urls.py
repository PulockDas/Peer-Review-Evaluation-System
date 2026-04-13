from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("courses/", include(("courses.urls", "courses"), namespace="courses")),
    path("assignments/", include(("assignments.urls", "assignments"), namespace="assignments")),
    path("submissions/", include(("submissions.urls", "submissions"), namespace="submissions")),
    path("rubrics/", include(("rubrics.urls", "rubrics"), namespace="rubrics")),
    path("reviews/", include(("reviews.urls", "reviews"), namespace="reviews")),
    path("grading/", include(("grading.urls", "grading"), namespace="grading")),
    path(
        "",
        TemplateView.as_view(template_name="home.html"),
        name="home",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

