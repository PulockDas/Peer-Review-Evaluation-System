from django.contrib import admin

from .models import Course, Enrollment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "instructor")
    search_fields = ("code", "title", "instructor__username", "instructor__email")
    list_filter = ("instructor",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("course", "student", "enrolled_at")
    search_fields = ("course__code", "course__title", "student__username", "student__email")
    list_filter = ("course",)

