from django.conf import settings
from django.db import models

from submissions.models import Submission


class FinalGrade(models.Model):
    """
    Stores the computed final grade for one submission.

    Lifecycle:
        CALCULATED  – grade has been computed but not yet visible to the student.
        RELEASED    – grade is visible to the student.
    """

    class Status(models.TextChoices):
        CALCULATED = "CALCULATED", "Calculated"
        RELEASED = "RELEASED", "Released"

    submission = models.OneToOneField(
        Submission,
        on_delete=models.CASCADE,
        related_name="final_grade",
    )
    numeric_score_100 = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Final normalised score on a 0–100 scale.",
    )
    letter_grade = models.CharField(max_length=2)
    gpa = models.DecimalField(max_digits=4, decimal_places=2)
    grade_status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CALCULATED,
    )
    calculated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of the last (re)calculation.",
    )
    released_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the grade was released to the student.",
    )

    class Meta:
        ordering = (
            "submission__assignment",
            "submission__student__last_name",
            "submission__student__first_name",
        )

    def __str__(self) -> str:
        return (
            f"{self.submission.student.username} — "
            f"{self.numeric_score_100} ({self.letter_grade})"
        )


class ReviewerAccuracy(models.Model):
    """
    Measures how closely one reviewer's total score for a submission
    matches the final average score for that submission.

    deviation_from_average: absolute difference between this reviewer's
        normalised score and the submission's final average (0–100 scale).
    accuracy_score: 100 − deviation, clamped to [0, 100].
        Higher is better; 100 means the reviewer was perfectly on average.
    """

    review = models.OneToOneField(
        "reviews.Review",
        on_delete=models.CASCADE,
        related_name="accuracy",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="accuracy_scores",
    )
    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="reviewer_accuracies",
    )
    deviation_from_average = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Absolute difference from the submission's average score (0–100 scale).",
    )
    accuracy_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="100 − deviation, clamped to [0, 100].",
    )
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-accuracy_score",)

    def __str__(self) -> str:
        return (
            f"{self.reviewer.username} accuracy={self.accuracy_score} "
            f"on {self.submission}"
        )
