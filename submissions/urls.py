from django.urls import path

from .views import InstructorSubmissionListView, StudentSubmitView

app_name = "submissions"

urlpatterns = [
    path(
        "assignment/<int:assignment_id>/submit/",
        StudentSubmitView.as_view(),
        name="submit",
    ),
    path(
        "assignment/<int:assignment_id>/",
        InstructorSubmissionListView.as_view(),
        name="assignment_submissions",
    ),
]
