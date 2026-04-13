import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("reviews", "0003_rework_review_add_reviewcriterionscore"),
        ("submissions", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="FinalGrade",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "submission",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="final_grade",
                        to="submissions.submission",
                    ),
                ),
                (
                    "numeric_score_100",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Final normalised score on a 0\u2013100 scale.",
                        max_digits=5,
                    ),
                ),
                ("letter_grade", models.CharField(max_length=2)),
                ("gpa", models.DecimalField(decimal_places=2, max_digits=4)),
                (
                    "grade_status",
                    models.CharField(
                        choices=[("CALCULATED", "Calculated"), ("RELEASED", "Released")],
                        default="CALCULATED",
                        max_length=20,
                    ),
                ),
                (
                    "calculated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp of the last (re)calculation.",
                    ),
                ),
                (
                    "released_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp when the grade was released to the student.",
                        null=True,
                    ),
                ),
            ],
            options={
                "ordering": (
                    "submission__assignment",
                    "submission__student__last_name",
                    "submission__student__first_name",
                ),
            },
        ),
        migrations.CreateModel(
            name="ReviewerAccuracy",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "review",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accuracy",
                        to="reviews.review",
                    ),
                ),
                (
                    "reviewer",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="accuracy_scores",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "submission",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviewer_accuracies",
                        to="submissions.submission",
                    ),
                ),
                (
                    "deviation_from_average",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Absolute difference from the submission's average score (0\u2013100 scale).",
                        max_digits=5,
                    ),
                ),
                (
                    "accuracy_score",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="100 \u2212 deviation, clamped to [0, 100].",
                        max_digits=5,
                    ),
                ),
                ("calculated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ("-accuracy_score",),
            },
        ),
    ]
