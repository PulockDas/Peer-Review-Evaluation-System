from django.urls import path

from .views import (
    AllocationView,
    InstructorMonitorView,
    InstructorReviewDetailView,
    MyReviewsListView,
    ReviewFormView,
)

app_name = "reviews"

urlpatterns = [
    # Student: list of assigned reviews
    path("my/", MyReviewsListView.as_view(), name="my_reviews"),

    # Student: open and submit a review (anonymous token)
    path("<uuid:token>/", ReviewFormView.as_view(), name="review_form"),

    # Instructor: monitor review completion for an assignment
    path(
        "assignment/<int:assignment_id>/monitor/",
        InstructorMonitorView.as_view(),
        name="monitor",
    ),

    # Instructor: view one submitted review in detail
    path(
        "inspect/<int:review_id>/",
        InstructorReviewDetailView.as_view(),
        name="review_inspect",
    ),

    # Instructor: manage reviewer allocation
    path(
        "assignment/<int:assignment_id>/allocate/",
        AllocationView.as_view(),
        name="allocate",
    ),
]
