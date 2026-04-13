from django.urls import path

from .views import (
    CriterionCreateView,
    CriterionDeleteView,
    CriterionUpdateView,
    RubricCreateView,
    RubricDetailView,
)

app_name = "rubrics"

urlpatterns = [
    # Rubric detail / landing (instructor & student)
    path(
        "assignment/<int:assignment_id>/",
        RubricDetailView.as_view(),
        name="detail",
    ),
    # Rubric setup (instructor — redirected here automatically when none exists)
    path(
        "assignment/<int:assignment_id>/create/",
        RubricCreateView.as_view(),
        name="create",
    ),
    # Criteria management (instructor only)
    path(
        "<int:rubric_id>/criteria/add/",
        CriterionCreateView.as_view(),
        name="criterion_add",
    ),
    path(
        "criteria/<int:criterion_id>/edit/",
        CriterionUpdateView.as_view(),
        name="criterion_edit",
    ),
    path(
        "criteria/<int:criterion_id>/delete/",
        CriterionDeleteView.as_view(),
        name="criterion_delete",
    ),
]
