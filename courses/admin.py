from django.contrib import admin

from .models import Course, Enrollment


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "instructor_name", "enrollment_count")
    list_filter = ("instructor",)
    search_fields = (
        "code",
        "title",
        "instructor__username",
        "instructor__first_name",
        "instructor__last_name",
        "instructor__email",
    )
    ordering = ("code",)

    @admin.display(description="Instructor", ordering="instructor__last_name")
    def instructor_name(self, obj):
        return obj.instructor.get_full_name() or obj.instructor.username

    @admin.display(description="Enrollments")
    def enrollment_count(self, obj):
        return obj.enrollments.count()


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("course", "student_name", "student_reg_no", "enrolled_at")
    list_filter = ("course",)
    search_fields = (
        "course__code",
        "course__title",
        "student__username",
        "student__first_name",
        "student__last_name",
        "student__email",
        "student__reg_no",
    )
    ordering = ("-enrolled_at",)
    readonly_fields = ("enrolled_at",)

    @admin.display(description="Student", ordering="student__last_name")
    def student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username

    @admin.display(description="Reg. no.", ordering="student__reg_no")
    def student_reg_no(self, obj):
        return obj.student.reg_no or "—"
