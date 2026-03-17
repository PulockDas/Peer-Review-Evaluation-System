from django.conf import settings
from django.db import models

from assignments.models import Assignment


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    content = models.TextField(blank=True)

    class Meta:
        ordering = ("-submitted_at",)
        unique_together = ("assignment", "student")

    def __str__(self) -> str:
        return f"{self.student.username} -> {self.assignment}"

