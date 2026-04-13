from django.contrib import admin

from .models import Rubric, RubricCriterion


class RubricCriterionInline(admin.TabularInline):
    model = RubricCriterion
    extra = 1
    fields = ("order", "criterion_name", "max_marks", "weight", "criterion_description")
    ordering = ("order",)


@admin.register(Rubric)
class RubricAdmin(admin.ModelAdmin):
    list_display = ("assignment", "course", "criterion_count", "total_weight", "updated_at")
    search_fields = (
        "assignment__title",
        "assignment__course__code",
        "assignment__course__title",
        "title",
    )
    list_filter = ("assignment__course",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [RubricCriterionInline]

    @admin.display(description="Course", ordering="assignment__course__code")
    def course(self, obj):
        return obj.assignment.course.code

    @admin.display(description="Criteria")
    def criterion_count(self, obj):
        return obj.criteria.count()

    @admin.display(description="Total weight (%)")
    def total_weight(self, obj):
        return obj.total_weight()


@admin.register(RubricCriterion)
class RubricCriterionAdmin(admin.ModelAdmin):
    list_display = ("criterion_name", "rubric", "max_marks", "weight", "order")
    search_fields = (
        "criterion_name",
        "rubric__assignment__title",
        "rubric__assignment__course__code",
    )
    list_filter = ("rubric__assignment__course",)
    ordering = ("rubric", "order")
