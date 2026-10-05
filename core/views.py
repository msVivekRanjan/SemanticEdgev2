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
    """Support & Contact page view."""

    template_name = "core/book_demo.html"

    def get(self, request):
        topic_param = request.GET.get("topic", request.GET.get("service", ""))
        initial = {}
        if topic_param in ["technical", "support"]:
            initial["query_type"] = "technical_support"
        elif topic_param in ["project", "deployment", "vehicles_people", "restricted_area"]:
            initial["query_type"] = "project_deployment"
        elif topic_param in ["docs", "documentation"]:
            initial["query_type"] = "documentation"

        form = DemoRequestForm(initial=initial)
        return render(request, self.template_name, {
            "form": form,
            "submitted": False,
        })

    def post(self, request):
        form = DemoRequestForm(request.POST)
        if form.is_valid():
            contact_req = form.save()
            messages.success(
                request,
                f"Thank you, {contact_req.full_name}! Your message has been received. Our team will get back to you within 24 hours.",
            )
            return render(request, self.template_name, {
                "form": DemoRequestForm(),
                "submitted": True,
                "contact_req": contact_req,
            })
        return render(request, self.template_name, {
            "form": form,
            "submitted": False,
        })
