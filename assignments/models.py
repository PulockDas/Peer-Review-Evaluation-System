from django.db import models

from courses.models import Course


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()

    class Meta:
        ordering = ("due_date",)

    def __str__(self) -> str:
        return f"{self.course.code}: {self.title}"

