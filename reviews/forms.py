from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["overall_comment"]
        widgets = {
            "overall_comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Overall feedback on this submission…",
                }
            ),
        }
        labels = {"overall_comment": "Overall comment (optional)"}


class CriterionScoreForm(forms.Form):
    """
    Per-criterion score + comment form.
    Pass max_marks= at construction so validation knows the upper bound.
    Use a unique prefix per criterion to avoid field name collisions.
    """

    score = forms.DecimalField(
        max_digits=6,
        decimal_places=2,
        label="Score",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "min": "0", "step": "0.01"}
        ),
    )
    comment = forms.CharField(
        required=False,
        label="Comment (optional)",
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Optional feedback for this criterion…",
            }
        ),
    )

    def __init__(self, *args, max_marks=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_marks = max_marks
        if max_marks is not None:
            self.fields["score"].widget.attrs["max"] = str(max_marks)

    def clean_score(self):
        score = self.cleaned_data.get("score")
        if score is None:
            return score
        if score < 0:
            raise forms.ValidationError("Score cannot be negative.")
        if self.max_marks is not None and score > self.max_marks:
            raise forms.ValidationError(
                f"Score cannot exceed the maximum of {self.max_marks}."
            )
        return score
