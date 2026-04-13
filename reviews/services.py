"""
Reviewer allocation service.

All allocation logic lives here — views stay thin.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from assignments.models import Assignment

REVIEWS_PER_SUBMISSION = 3


class AllocationError(Exception):
    """Raised when reviewer allocation cannot be completed."""


def allocate_reviewers(assignment: "Assignment") -> list:
    """
    Assign exactly REVIEWS_PER_SUBMISSION reviewers to every submission
    for *assignment* using a greedy, workload-balanced algorithm.

    Rules
    -----
    - Reviewers must be students enrolled in the assignment's course.
    - A reviewer cannot be assigned to their own submission.
    - The same reviewer cannot be assigned twice to the same submission
      (enforced by the model constraint; the algorithm never creates duplicates).
    - Workload is balanced: at each step the eligible reviewer with the
      fewest existing assignments is picked. Ties are broken by primary key
      for determinism.

    Returns
    -------
    list[ReviewAssignment]
        The newly created ReviewAssignment objects.

    Raises
    ------
    AllocationError
        If allocation is impossible (no submissions, too few students, etc.).
    """
    from accounts.models import User
    from courses.models import Enrollment
    from submissions.models import Submission

    from .models import ReviewAssignment

    # ------------------------------------------------------------------
    # 1. Gather data
    # ------------------------------------------------------------------
    submissions = list(
        Submission.objects.filter(assignment=assignment)
        .select_related("student")
        .order_by("pk")
    )
    if not submissions:
        raise AllocationError("No submissions found for this assignment.")

    # All enrolled students (role=STUDENT) are eligible reviewers.
    enrolled_students = list(
        User.objects.filter(
            enrollments__course=assignment.course,
            role=User.Roles.STUDENT,
        )
        .distinct()
        .order_by("pk")
    )

    # ------------------------------------------------------------------
    # 2. Validate feasibility
    # ------------------------------------------------------------------
    if len(enrolled_students) <= REVIEWS_PER_SUBMISSION:
        raise AllocationError(
            f"At least {REVIEWS_PER_SUBMISSION + 1} enrolled students are required "
            f"to assign {REVIEWS_PER_SUBMISSION} reviewers per submission. "
            f"Currently enrolled: {len(enrolled_students)}."
        )

    for sub in submissions:
        eligible_count = sum(1 for s in enrolled_students if s.pk != sub.student_id)
        if eligible_count < REVIEWS_PER_SUBMISSION:
            raise AllocationError(
                f"Submission by '{sub.student.username}' has only {eligible_count} "
                f"eligible reviewer(s), but {REVIEWS_PER_SUBMISSION} are required. "
                f"Enrol more students in the course before allocating."
            )

    # ------------------------------------------------------------------
    # 3. Greedy balanced allocation
    # ------------------------------------------------------------------
    # workload[student_pk] = number of review assignments so far
    workload: dict[int, int] = {s.pk: 0 for s in enrolled_students}
    student_by_pk: dict[int, object] = {s.pk: s for s in enrolled_students}

    to_create: list[ReviewAssignment] = []

    for sub in submissions:
        # Eligible reviewers for this submission (cannot review own work)
        eligible_pks = [s.pk for s in enrolled_students if s.pk != sub.student_id]

        # Sort by (workload, pk) so ties are broken deterministically
        eligible_pks.sort(key=lambda pk: (workload[pk], pk))

        selected_pks = eligible_pks[:REVIEWS_PER_SUBMISSION]

        for reviewer_pk in selected_pks:
            to_create.append(
                ReviewAssignment(
                    submission=sub,
                    reviewer=student_by_pk[reviewer_pk],
                )
            )
            workload[reviewer_pk] += 1

    # ------------------------------------------------------------------
    # 4. Persist (ignore_conflicts=False so integrity errors surface)
    # ------------------------------------------------------------------
    created = ReviewAssignment.objects.bulk_create(to_create)
    return created


def delete_allocations(assignment: "Assignment") -> int:
    """
    Delete all ReviewAssignments for *assignment*.
    Returns the number of rows deleted.
    """
    from .models import ReviewAssignment

    deleted, _ = ReviewAssignment.objects.filter(
        submission__assignment=assignment
    ).delete()
    return deleted
