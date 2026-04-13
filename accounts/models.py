from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        INSTRUCTOR = "INSTRUCTOR", "Instructor"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.STUDENT,
        help_text="Determines the permissions and UI within the system.",
    )
    reg_no = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Registration number",
        help_text="Official student registration number. Leave blank for instructors and admins.",
    )

    def save(self, *args, **kwargs):
        # Normalise reg_no so uniqueness is always case-insensitive and
        # leading/trailing whitespace can never create phantom duplicates.
        if self.reg_no:
            self.reg_no = self.reg_no.strip().upper()
        else:
            self.reg_no = None  # coerce empty string → NULL for the unique index
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.username
