from django import forms

from .models import Rubric, RubricCriterion


class RubricForm(forms.ModelForm):
    class Meta:
        model = Rubric
        fields = ["title", "description"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. Essay evaluation rubric"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Optional overview…"}
            ),
        }


class RubricCriterionForm(forms.ModelForm):
    class Meta:
        model = RubricCriterion
        fields = ["criterion_name", "criterion_description", "max_marks", "weight", "order"]
        widgets = {
            "criterion_name": forms.TextInput(attrs={"class": "form-control"}),
            "criterion_description": forms.Textarea(
                attrs={"class": "form-control", "rows": 3}
            ),
            "max_marks": forms.NumberInput(attrs={"class": "form-control", "min": "0.01", "step": "0.01"}),
            "weight": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "max": "100", "step": "0.01"}
            ),
            "order": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        }
        labels = {
            "criterion_name": "Criterion name",
            "criterion_description": "Description",
            "max_marks": "Max marks",
            "weight": "Weight (%)",
            "order": "Display order",
        }

    def clean_max_marks(self):
        value = self.cleaned_data.get("max_marks")
        if value is not None and value <= 0:
            raise forms.ValidationError("Max marks must be greater than zero.")
        return value

    def clean_weight(self):
        value = self.cleaned_data.get("weight")
        if value is not None and not (0 <= value <= 100):
            raise forms.ValidationError("Weight must be between 0 and 100.")
        return value
