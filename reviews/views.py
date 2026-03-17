from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Review


class ReviewListView(LoginRequiredMixin, ListView):
    model = Review
    template_name = "reviews/review_list.html"
    context_object_name = "reviews"

