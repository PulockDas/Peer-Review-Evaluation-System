from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from accounts.mixins import RoleRequiredMixin
from accounts.models import User

from .forms import CourseForm, EnrollmentForm
from .models import Course, Enrollment


class CourseIndexView(LoginRequiredMixin, View):
    """
    Role-aware entrypoint for /courses/.
    """

    def get(self, request, *args, **kwargs):
        role = getattr(request.user, "role", User.Roles.STUDENT)
        if role == User.Roles.INSTRUCTOR:
            return redirect("courses:instructor_list")
        if role == User.Roles.STUDENT:
            return redirect("courses:student_list")
        return redirect("accounts:dashboard")


class InstructorCourseListView(RoleRequiredMixin, ListView):
    allowed_roles = (User.Roles.INSTRUCTOR,)
    model = Course
    template_name = "courses/instructor_course_list.html"
    context_object_name = "courses"

    def get_queryset(self) -> QuerySet[Course]:
        return Course.objects.filter(instructor=self.request.user).order_by("code")


class StudentCourseListView(RoleRequiredMixin, ListView):
    allowed_roles = (User.Roles.STUDENT,)
    model = Course
    template_name = "courses/student_course_list.html"
    context_object_name = "courses"

    def get_queryset(self) -> QuerySet[Course]:
        return Course.objects.filter(enrollments__student=self.request.user).distinct().order_by("code")


class CourseCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Roles.INSTRUCTOR,)
    model = Course
    form_class = CourseForm
    template_name = "courses/course_form.html"

    def form_valid(self, form):
        form.instance.instructor = self.request.user
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("courses:detail", kwargs={"pk": self.object.pk})


class CourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = "courses/course_detail.html"
    context_object_name = "course"

    def get_object(self, queryset=None) -> Course:
        course: Course = super().get_object(queryset)
        role = getattr(self.request.user, "role", None)
        if role == User.Roles.INSTRUCTOR and course.instructor_id != self.request.user.id:
            raise Http404
        if role == User.Roles.STUDENT and not Enrollment.objects.filter(
            course=course, student=self.request.user
        ).exists():
            raise Http404
        return course

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_instructor_owner"] = self.request.user.is_authenticated and (
            getattr(self.request.user, "role", None) == User.Roles.INSTRUCTOR
            and self.object.instructor_id == self.request.user.id
        )
        if ctx["is_instructor_owner"]:
            ctx["enrollments"] = Enrollment.objects.filter(course=self.object).select_related("student")
        return ctx


class EnrollmentCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Roles.INSTRUCTOR,)
    model = Enrollment
    form_class = EnrollmentForm
    template_name = "courses/enroll_student.html"

    def dispatch(self, request, *args, **kwargs):
        self.course = Course.objects.filter(pk=kwargs["pk"], instructor=request.user).first()
        if not self.course:
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.course = self.course
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("courses:detail", kwargs={"pk": self.course.pk})

