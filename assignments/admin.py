from django.contrib import admin

from .models import Assignment


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ("title", "course_code", "due_date", "submission_count", "has_rubric")
    list_filter = ("course", "due_date")
    search_fields = ("title", "course__code", "course__title")
    ordering = ("-due_date",)
    date_hierarchy = "due_date"

    @admin.display(description="Course", ordering="course__code")
    def course_code(self, obj):
        return obj.course.code

    @admin.display(description="Submissions")
    def submission_count(self, obj):
        return obj.submissions.count()

    @admin.display(description="Rubric", boolean=True)
    def has_rubric(self, obj):
        try:
            return obj.rubric is not None
        except Exception:
            return False
