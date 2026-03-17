from django.db import models

from submissions.models import Submission


class Grade(models.Model):
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name="grade")
    final_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    letter_grade = models.CharField(max_length=2, blank=True)
    released = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.submission} -> {self.final_score}"

