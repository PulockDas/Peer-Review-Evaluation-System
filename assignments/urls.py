from django.urls import path

from .views import AssignmentCreateView, CourseAssignmentListView

app_name = "assignments"

urlpatterns = [
    path("course/<int:course_id>/", CourseAssignmentListView.as_view(), name="list"),
    path("course/<int:course_id>/create/", AssignmentCreateView.as_view(), name="create"),
]

