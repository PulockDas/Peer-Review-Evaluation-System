from django.contrib import admin

from .models import Review, ReviewAssignment, ReviewCriterionScore


class ReviewCriterionScoreInline(admin.TabularInline):
    model = ReviewCriterionScore
    extra = 0
    fields = ("criterion", "score", "comment")
    readonly_fields = ("criterion",)


@admin.register(ReviewAssignment)
class ReviewAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "reviewer",
        "submission_student",
        "assignment",
        "course",
        "review_status",
        "assigned_at",
    )
    list_filter = (
        "review_status",
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
        "submission__assignment__title",
    )
    readonly_fields = ("assigned_at", "anonymous_token")
    ordering = ("submission__assignment", "submission__student__last_name", "reviewer__last_name")

    @admin.display(description="Author", ordering="submission__student__last_name")
    def submission_student(self, obj):
        return obj.submission.student.get_full_name() or obj.submission.student.username

    @admin.display(description="Assignment", ordering="submission__assignment__title")
    def assignment(self, obj):
        return obj.submission.assignment.title

    @admin.display(description="Course", ordering="submission__assignment__course__code")
    def course(self, obj):
        return obj.submission.assignment.course.code


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "pk",
        "reviewer",
        "submission_author",
        "assignment",
        "total_score",
        "submitted_at",
    )
    list_filter = (
        "review_assignment__submission__assignment__course",
        "review_assignment__submission__assignment",
    )
    search_fields = (
        "review_assignment__reviewer__username",
        "review_assignment__reviewer__reg_no",
        "review_assignment__submission__student__username",
        "review_assignment__submission__assignment__title",
    )
    readonly_fields = ("submitted_at", "total_score")
    inlines = [ReviewCriterionScoreInline]

    @admin.display(description="Reviewer")
    def reviewer(self, obj):
        return obj.review_assignment.reviewer.get_full_name() or obj.review_assignment.reviewer.username

    @admin.display(description="Author")
    def submission_author(self, obj):
        s = obj.review_assignment.submission.student
        return s.get_full_name() or s.username

    @admin.display(description="Assignment")
    def assignment(self, obj):
        return obj.review_assignment.submission.assignment.title


@admin.register(ReviewCriterionScore)
class ReviewCriterionScoreAdmin(admin.ModelAdmin):
    list_display = ("pk", "review", "criterion", "score")
    list_filter = (
        "review__review_assignment__submission__assignment__course",
    )
    search_fields = (
        "criterion__criterion_name",
        "review__review_assignment__reviewer__username",
    )
    readonly_fields = ("review", "criterion")
