from django import forms

from .models import Submission


class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ["file", "content"]
        widgets = {
            "file": forms.FileInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Optional notes or comments for your instructor…",
                }
            ),
        }
        labels = {
            "file": "Upload file",
            "content": "Notes (optional)",
        }
