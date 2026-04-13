from django.urls import path

from .views import (
    GradeManagementView,
    ReviewerAccuracyView,
    StudentGradeListView,
    StudentResultView,
)

app_name = "grading"

urlpatterns = [
    # Instructor: grade management for one assignment
    path(
        "assignment/<int:assignment_id>/",
        GradeManagementView.as_view(),
        name="manage",
    ),

    # Instructor: reviewer accuracy for one assignment
    path(
        "assignment/<int:assignment_id>/accuracy/",
        ReviewerAccuracyView.as_view(),
        name="accuracy",
    ),

    # Student: list all released grades
    path("my/", StudentGradeListView.as_view(), name="my_grades"),

    # Student: detailed result for one submission
    path(
        "submission/<int:submission_id>/result/",
        StudentResultView.as_view(),
        name="result",
    ),
]
