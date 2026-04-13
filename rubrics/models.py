from django.db import models

from assignments.models import Assignment


class Rubric(models.Model):
    """One rubric per assignment (enforced by the OneToOneField)."""

    assignment = models.OneToOneField(
        Assignment,
        on_delete=models.CASCADE,
        related_name="rubric",
    )
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Rubric: {self.assignment}"

    def total_max_marks(self):
        return sum(c.max_marks for c in self.criteria.all())

    def total_weight(self):
        return sum(c.weight for c in self.criteria.all())


class RubricCriterion(models.Model):
    """A single scored criterion belonging to a rubric."""

    rubric = models.ForeignKey(Rubric, on_delete=models.CASCADE, related_name="criteria")
    criterion_name = models.CharField(max_length=255)
    criterion_description = models.TextField(blank=True)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2)
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Percentage weight of this criterion (0 – 100).",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within the rubric (lower numbers appear first).",
    )

    class Meta:
        ordering = ("order", "pk")
        constraints = [
            models.CheckConstraint(
                check=models.Q(max_marks__gt=0),
                name="rubric_criterion_max_marks_positive",
            ),
            models.CheckConstraint(
                check=models.Q(weight__gte=0) & models.Q(weight__lte=100),
                name="rubric_criterion_weight_0_to_100",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.criterion_name} ({self.rubric.assignment})"
