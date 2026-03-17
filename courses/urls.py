from django.urls import path

from .views import (
    CourseCreateView,
    CourseDetailView,
    CourseIndexView,
    EnrollmentCreateView,
    InstructorCourseListView,
    StudentCourseListView,
)

app_name = "courses"

urlpatterns = [
    path("", CourseIndexView.as_view(), name="index"),
    path("instructor/", InstructorCourseListView.as_view(), name="instructor_list"),
    path("student/", StudentCourseListView.as_view(), name="student_list"),
    path("create/", CourseCreateView.as_view(), name="create"),
    path("<int:pk>/", CourseDetailView.as_view(), name="detail"),
    path("<int:pk>/enroll/", EnrollmentCreateView.as_view(), name="enroll"),
]

