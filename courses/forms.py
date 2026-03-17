from django import forms

from accounts.models import User
from .models import Course, Enrollment


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ["code", "title", "description"]
        widgets = {
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. CS101"}),
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Introduction to Computing"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["student"]
        widgets = {
            "student": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["student"].queryset = User.objects.filter(role=User.Roles.STUDENT).order_by("username")

