"""
Grade scale configuration.

Edit GRADE_SCALE to change the mapping from numeric score (0–100) to
letter grade and GPA points without touching any business logic.

Each entry is (minimum_score_inclusive, letter_grade, gpa_points).
Entries must be sorted from highest to lowest threshold.
"""

from decimal import Decimal

GRADE_SCALE: list[tuple[int, str, Decimal]] = [
    (90, "A", Decimal("4.00")),
    (80, "B", Decimal("3.00")),
    (70, "C", Decimal("2.00")),
    (60, "D", Decimal("1.00")),
    ( 0, "F", Decimal("0.00")),
]


def get_grade(score: Decimal) -> tuple[str, Decimal]:
    """
    Return (letter_grade, gpa_points) for a numeric score on the 0–100 scale.

    Iterates from the highest threshold downward; the first entry whose
    minimum threshold is <= score wins.
    """
    for threshold, letter, gpa in GRADE_SCALE:
        if score >= Decimal(str(threshold)):
            return letter, gpa
    return "F", Decimal("0.00")
