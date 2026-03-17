from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Submission


class SubmissionListView(LoginRequiredMixin, ListView):
    model = Submission
    template_name = "submissions/submission_list.html"
    context_object_name = "submissions"

