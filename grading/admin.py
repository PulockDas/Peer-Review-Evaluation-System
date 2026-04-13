from django.contrib import admin

from .models import FinalGrade, ReviewerAccuracy


@admin.register(FinalGrade)
class FinalGradeAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "assignment",
        "course",
        "numeric_score_100",
        "letter_grade",
        "gpa",
        "grade_status",
        "calculated_at",
        "released_at",
    )
    list_filter = (
        "grade_status",
        "letter_grade",
        "submission__assignment__course",
        "submission__assignment",
    )
    search_fields = (
        "submission__student__username",
        "submission__student__first_name",
        "submission__student__last_name",
        "submission__student__reg_no",
        "submission__assignment__title",
        "submission__assignment__course__code",
    )
    readonly_fields = ("calculated_at", "released_at")
    ordering = (
        "submission__assignment__course__code",
        "submission__assignment__title",
        "submission__student__last_name",
    )

    @admin.display(description="Student", ordering="submission__student__last_name")
    def student(self, obj):
        u = obj.submission.student
        return u.get_full_name() or u.username

    @admin.display(description="Assignment", ordering="submission__assignment__title")
    def assignment(self, obj):
        return obj.submission.assignment.title

    @admin.display(description="Course", ordering="submission__assignment__course__code")
    def course(self, obj):
        return obj.submission.assignment.course.code


@admin.register(ReviewerAccuracy)
class ReviewerAccuracyAdmin(admin.ModelAdmin):
    list_display = (
        "reviewer",
        "submission_author",
        "assignment",
        "accuracy_score",
        "deviation_from_average",
        "calculated_at",
    )
    list_filter = (
        "submission__assignment__course",
        "submission__assignment",
    )
    search_fields = (
        "reviewer__username",
        "reviewer__first_name",
        "reviewer__last_name",
        "reviewer__reg_no",
        "submission__student__username",
        "submission__student__reg_no",
    )
    readonly_fields = ("calculated_at",)
    ordering = ("-accuracy_score",)

    @admin.display(description="Reviewer", ordering="reviewer__last_name")
    def reviewer_display(self, obj):
        return obj.reviewer.get_full_name() or obj.reviewer.username

    @admin.display(description="Author (submission)", ordering="submission__student__last_name")
    def submission_author(self, obj):
        u = obj.submission.student
        return u.get_full_name() or u.username

    @admin.display(description="Assignment")
    def assignment(self, obj):
        return obj.submission.assignment.title
