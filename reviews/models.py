import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from submissions.models import Submission


class ReviewAssignment(models.Model):
    """
    Records that a specific student has been assigned to review a submission.
    The anonymous_token is used in student-facing URLs so that neither the
    reviewer's nor the author's identity is revealed through the URL.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        COMPLETED = "COMPLETED", "Completed"

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="review_assignments",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="review_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    review_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    anonymous_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        help_text="Opaque token used in anonymous student-facing review URLs.",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["submission", "reviewer"],
                name="unique_reviewer_per_submission",
            ),
        ]
        ordering = ("submission", "reviewer__last_name", "reviewer__first_name")

    def clean(self):
        if self.reviewer_id and self.submission_id:
            if self.reviewer_id == self.submission.student_id:
                raise ValidationError(
                    "A reviewer cannot be assigned to review their own submission."
                )

    def __str__(self) -> str:
        return f"{self.reviewer.username} \u2192 {self.submission}"


class Review(models.Model):
    """
    A completed peer review submitted by the assigned reviewer.
    Linked one-to-one with ReviewAssignment.
    total_score is derived from the sum of ReviewCriterionScore.score values
    and is stored for easy querying/display.
    """

    review_assignment = models.OneToOneField(
        ReviewAssignment,
        on_delete=models.CASCADE,
        related_name="review",
    )
    overall_comment = models.TextField(
        blank=True,
        help_text="General feedback on the submission.",
    )
    total_score = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        default=0,
        help_text="Sum of all criterion scores (calculated automatically).",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-submitted_at",)

    def __str__(self) -> str:
        return (
            f"Review #{self.pk} by {self.review_assignment.reviewer.username}"
        )


class ReviewCriterionScore(models.Model):
    """
    Score awarded for a single rubric criterion within one peer review.
    """

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="criterion_scores",
    )
    criterion = models.ForeignKey(
        "rubrics.RubricCriterion",
        on_delete=models.CASCADE,
        related_name="scores",
    )
    score = models.DecimalField(max_digits=6, decimal_places=2)
    comment = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["review", "criterion"],
                name="unique_criterion_score_per_review",
            ),
            models.CheckConstraint(
                check=models.Q(score__gte=0),
                name="review_criterion_score_non_negative",
            ),
        ]
        ordering = ("criterion__order", "criterion__pk")

    def __str__(self) -> str:
        return f"{self.score} / {self.criterion.max_marks} on {self.criterion.criterion_name}"
