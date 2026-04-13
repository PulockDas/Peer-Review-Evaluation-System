from django.contrib import admin
from django.utils.html import format_html

from .models import Submission


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "assignment",
        "course",
        "status",
        "submitted_at",
        "updated_at",
        "has_file",
    )
    list_filter = ("status", "assignment__course")
    search_fields = (
        "student__username",
        "student__email",
        "student__first_name",
        "student__last_name",
        "assignment__title",
        "assignment__course__code",
    )
    readonly_fields = ("submitted_at", "updated_at", "file_link")
    ordering = ("-submitted_at",)

    fieldsets = (
        (
            None,
            {
                "fields": ("assignment", "student", "status"),
            },
        ),
        (
            "Submission content",
            {
                "fields": ("file", "file_link", "content"),
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("submitted_at", "updated_at"),
            },
        ),
    )

    @admin.display(description="Course", ordering="assignment__course__code")
    def course(self, obj):
        return obj.assignment.course.code

    @admin.display(description="File", boolean=True)
    def has_file(self, obj):
        return bool(obj.file)

    @admin.display(description="Current file")
    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.file.url, obj.file.name)
        return "—"
