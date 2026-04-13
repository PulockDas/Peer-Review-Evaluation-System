"""
Rework the Review model:
  - drop the old placeholder Review (submission FK + reviewer FK + score + comments)
  - recreate Review linked one-to-one to ReviewAssignment
  - add ReviewCriterionScore for per-criterion scoring
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reviews", "0002_reviewassignment"),
        ("rubrics", "0001_initial"),
    ]

    operations = [
        # 1. Drop the old placeholder Review table
        migrations.DeleteModel(name="Review"),

        # 2. Recreate Review with the new schema
        migrations.CreateModel(
            name="Review",
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
                    "review_assignment",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="review",
                        to="reviews.reviewassignment",
                    ),
                ),
                (
                    "overall_comment",
                    models.TextField(
                        blank=True,
                        help_text="General feedback on the submission.",
                    ),
                ),
                (
                    "total_score",
                    models.DecimalField(
                        decimal_places=2,
                        default=0,
                        help_text="Sum of all criterion scores (calculated automatically).",
                        max_digits=7,
                    ),
                ),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ("-submitted_at",),
            },
        ),

        # 3. Add ReviewCriterionScore
        migrations.CreateModel(
            name="ReviewCriterionScore",
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
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="criterion_scores",
                        to="reviews.review",
                    ),
                ),
                (
                    "criterion",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="scores",
                        to="rubrics.rubriccriterion",
                    ),
                ),
                (
                    "score",
                    models.DecimalField(decimal_places=2, max_digits=6),
                ),
                ("comment", models.TextField(blank=True)),
            ],
            options={
                "ordering": ("criterion__order", "criterion__pk"),
            },
        ),

        # 4. Constraints on ReviewCriterionScore
        migrations.AddConstraint(
            model_name="reviewcriterionscore",
            constraint=models.UniqueConstraint(
                fields=("review", "criterion"),
                name="unique_criterion_score_per_review",
            ),
        ),
        migrations.AddConstraint(
            model_name="reviewcriterionscore",
            constraint=models.CheckConstraint(
                check=models.Q(score__gte=0),
                name="review_criterion_score_non_negative",
            ),
        ),
    ]
