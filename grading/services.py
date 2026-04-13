"""
Grading service layer.

All calculation and release logic lives here; views remain thin.
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from assignments.models import Assignment

from .grade_scale import get_grade

REQUIRED_COMPLETED_REVIEWS = 3


class GradingError(Exception):
    """Raised when grade calculation cannot proceed."""


# ---------------------------------------------------------------------------
# Main calculation entry point
# ---------------------------------------------------------------------------

def calculate_grades_for_assignment(
    assignment: "Assignment",
    force: bool = False,
) -> tuple[int, int]:
    """
    Compute and persist FinalGrade + ReviewerAccuracy for every eligible
    submission of *assignment*.

    Eligibility rules
    -----------------
    - The assignment must have a rubric with a positive total max-marks.
    - The submission must have exactly REQUIRED_COMPLETED_REVIEWS completed
      reviews (default 3).
    - If force=False, submissions whose grade is already RELEASED are skipped.
      If force=True, released grades are recalculated (released_at is cleared,
      status reverts to CALCULATED).

    Returns
    -------
    (n_calculated, n_skipped)
    """
    from reviews.models import ReviewAssignment

    from .models import FinalGrade, ReviewerAccuracy

    # ------------------------------------------------------------------
    # 1. Validate rubric
    # ------------------------------------------------------------------
    try:
        rubric = assignment.rubric
    except Exception:
        raise GradingError(
            "This assignment has no rubric. "
            "Add a rubric with criteria before calculating grades."
        )

    total_max = Decimal(str(rubric.total_max_marks()))
    if total_max <= 0:
        raise GradingError(
            "The rubric has no criteria or all criteria have zero max marks. "
            "Add scored criteria to the rubric first."
        )

    # ------------------------------------------------------------------
    # 2. Gather submissions
    # ------------------------------------------------------------------
    from submissions.models import Submission

    submissions = list(
        Submission.objects.filter(assignment=assignment)
        .select_related("student")
        .prefetch_related("review_assignments__review__criterion_scores")
    )

    n_calculated = 0
    n_skipped = 0

    for submission in submissions:
        # Collect completed reviews for this submission
        completed_reviews = []
        for ra in submission.review_assignments.all():
            if ra.review_status == ReviewAssignment.Status.COMPLETED:
                try:
                    completed_reviews.append(ra.review)
                except Exception:
                    pass

        if len(completed_reviews) < REQUIRED_COMPLETED_REVIEWS:
            n_skipped += 1
            continue

        # Skip RELEASED grades unless force=True
        existing = FinalGrade.objects.filter(submission=submission).first()
        if (
            existing
            and existing.grade_status == FinalGrade.Status.RELEASED
            and not force
        ):
            n_skipped += 1
            continue

        # --------------------------------------------------------------
        # 3. Normalise each review's total to 0–100
        # --------------------------------------------------------------
        scored_pairs: list[tuple] = []  # (review, normalised_score)
        for review in completed_reviews:
            raw = Decimal(str(review.total_score))
            normalised = (raw / total_max * Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            # Clamp in case of floating-point edge cases
            normalised = max(Decimal("0"), min(Decimal("100"), normalised))
            scored_pairs.append((review, normalised))

        # --------------------------------------------------------------
        # 4. Final score = mean of normalised review scores
        # --------------------------------------------------------------
        avg = (
            sum(s for _, s in scored_pairs) / Decimal(len(scored_pairs))
        ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        avg = max(Decimal("0"), min(Decimal("100"), avg))

        letter, gpa = get_grade(avg)

        # --------------------------------------------------------------
        # 5. Persist FinalGrade
        # --------------------------------------------------------------
        if existing:
            existing.numeric_score_100 = avg
            existing.letter_grade = letter
            existing.gpa = gpa
            existing.grade_status = FinalGrade.Status.CALCULATED
            # Clear released_at if we are recalculating a released grade
            if existing.released_at is not None:
                existing.released_at = None
            existing.save()
        else:
            FinalGrade.objects.create(
                submission=submission,
                numeric_score_100=avg,
                letter_grade=letter,
                gpa=gpa,
            )

        # --------------------------------------------------------------
        # 6. Persist ReviewerAccuracy for each review
        # --------------------------------------------------------------
        for review, norm_score in scored_pairs:
            deviation = abs(norm_score - avg).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            accuracy = max(Decimal("0"), Decimal("100") - deviation).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            ReviewerAccuracy.objects.update_or_create(
                review=review,
                defaults={
                    "reviewer": review.review_assignment.reviewer,
                    "submission": submission,
                    "deviation_from_average": deviation,
                    "accuracy_score": accuracy,
                },
            )

        n_calculated += 1

    return n_calculated, n_skipped


# ---------------------------------------------------------------------------
# Release helpers
# ---------------------------------------------------------------------------

def release_grades(assignment: "Assignment") -> int:
    """
    Mark all CALCULATED grades for *assignment* as RELEASED.
    Returns the number of grades released.
    """
    from django.utils import timezone

    from .models import FinalGrade

    return FinalGrade.objects.filter(
        submission__assignment=assignment,
        grade_status=FinalGrade.Status.CALCULATED,
    ).update(grade_status=FinalGrade.Status.RELEASED, released_at=timezone.now())


def unrelease_grades(assignment: "Assignment") -> int:
    """
    Revert all RELEASED grades for *assignment* back to CALCULATED.
    Returns the number of grades reverted.
    """
    from .models import FinalGrade

    return FinalGrade.objects.filter(
        submission__assignment=assignment,
        grade_status=FinalGrade.Status.RELEASED,
    ).update(grade_status=FinalGrade.Status.CALCULATED, released_at=None)
