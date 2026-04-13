import re

from django.conf import settings
from django.db import models

from assignments.models import Assignment


def submission_upload_path(instance, filename):
    # Prefer the student's reg_no for a human-readable folder name.
    # Fall back to the numeric PK if reg_no is somehow absent.
    reg = getattr(instance.student, "reg_no", None) or f"id_{instance.student_id}"
    # Strip any character that isn't a word char or hyphen so the path is
    # safe on every OS regardless of what the reg_no string contains.
    safe_reg = re.sub(r"[^\w\-]", "_", str(reg))
    return f"submissions/assignment_{instance.assignment_id}/{safe_reg}/{filename}"


class Submission(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        LATE = "LATE", "Late"

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    file = models.FileField(upload_to=submission_upload_path, blank=True)
    content = models.TextField(blank=True, help_text="Optional notes or comments for your submission.")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-submitted_at",)
        unique_together = ("assignment", "student")

    def __str__(self) -> str:
        return f"{self.student.username} → {self.assignment}"
