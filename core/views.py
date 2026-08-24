"""core/views.py — Public marketing pages."""

from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "core/home.html"
