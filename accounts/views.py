"""
accounts/views.py
-----------------
Authentication & Registration views for SemanticEdge.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View

from nvr.models import Camera
from .forms import UserRegistrationForm


class RegisterView(View):
    """Handles new user self-registration."""

    template_name = "accounts/register.html"

    def get(self, request):
        if request.user.is_authenticated:
            return redirect("nvr:live")
        form = UserRegistrationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        if request.user.is_authenticated:
            return redirect("nvr:live")
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.save()

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
            messages.success(request, f"Welcome to SemanticEdge, {user.username}! Your monitoring console is ready.")
            return redirect("nvr:live")

        return render(request, self.template_name, {"form": form})
