from typing import Iterable

from django.contrib.auth.mixins import AccessMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect


class RoleRequiredMixin(AccessMixin):
    allowed_roles: Iterable[str] = ()

    def dispatch(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        if self.allowed_roles and getattr(request.user, "role", None) not in self.allowed_roles:
            return redirect("accounts:dashboard")

        return super().dispatch(request, *args, **kwargs)

