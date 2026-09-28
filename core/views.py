"""
core/views.py
-------------
Public marketing, services catalogue, and demo booking views.
"""

from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import TemplateView

from .forms import DemoRequestForm


class HomeView(TemplateView):
    template_name = "core/home.html"


class BookDemoView(View):
    """Book a Demo / Enterprise Contact page."""

    template_name = "core/book_demo.html"

    def get(self, request):
        service_param = request.GET.get("service", "")
        initial = {}
        if service_param == "vehicles_people":
            initial["service_vehicles_people"] = True
        elif service_param == "object_count":
            initial["service_object_count"] = True

        form = DemoRequestForm(initial=initial)
        return render(request, self.template_name, {
            "form": form,
            "selected_service": service_param,
            "submitted": False,
        })

    def post(self, request):
        form = DemoRequestForm(request.POST)
        if form.is_valid():
            demo_req = form.save()
            messages.success(
                request,
                f"Thank you, {demo_req.full_name}! Your demo request for {demo_req.company_name} has been received. Our solutions team will contact you within 24 hours.",
            )
            return render(request, self.template_name, {
                "form": DemoRequestForm(),
                "submitted": True,
                "demo_req": demo_req,
            })
        return render(request, self.template_name, {
            "form": form,
            "submitted": False,
        })
