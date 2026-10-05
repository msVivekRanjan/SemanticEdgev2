"""
accounts/views.py
-----------------
Authentication & Registration views for SemanticEdge.

In SHOWCASE_MODE the NVR-specific imports (Camera model, nvr:live redirect)
are conditionally skipped so that OpenCV/YOLO deps are never pulled in.
"""

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from .forms import UserRegistrationForm

# Conditionally import NVR models to avoid loading Edge-AI deps in Showcase Mode.
_NVR_AVAILABLE = not getattr(settings, "SHOWCASE_MODE", False)
if _NVR_AVAILABLE:
    from nvr.models import Camera


class RegisterView(View):
    """Handles new user self-registration."""

    template_name = "accounts/register.html"

    def _post_auth_redirect(self):
        """Return the appropriate post-login destination."""
        if _NVR_AVAILABLE:
            return redirect("nvr:live")
        return redirect("/")

    def get(self, request):
        if request.user.is_authenticated:
            return self._post_auth_redirect()
        form = UserRegistrationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        if request.user.is_authenticated:
            return self._post_auth_redirect()
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

            if _NVR_AVAILABLE:
                # Provision default camera for immediate usability
                Camera.objects.create(
                    owner=user,
                    name="Primary Sensor (Webcam 0)",
                    source_url="0",
                    tracker_enabled=True,
                    is_active=True,
                )

            # Auto-login newly registered user
            login(request, user)
            messages.success(
                request,
                f"Welcome to SemanticEdge, {user.username}! "
                + ("Your monitoring console is ready." if _NVR_AVAILABLE else ""),
            )
            return self._post_auth_redirect()

        return render(request, self.template_name, {"form": form})
