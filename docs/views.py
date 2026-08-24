"""
docs/views.py
-------------
DocsListView  — redirects to the first doc page, or shows empty state.
DocDetailView — renders a single DocPage (Markdown → HTML).
"""

from itertools import groupby

import markdown2
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView

from .models import DocPage


def _render_markdown(raw: str) -> str:
    """Convert Markdown to HTML with syntax highlighting via Pygments."""
    return markdown2.markdown(
        raw,
        extras=[
            "fenced-code-blocks",
            "code-friendly",
            "tables",
            "header-ids",
            "strike",
            "task_list",
        ],
    )


def _get_sidebar_groups() -> list[dict]:
    """Return all docs grouped by category for the sidebar."""
    pages = DocPage.objects.order_by("category", "order", "title")
    groups = []
    for category, items in groupby(pages, key=lambda p: p.category):
        groups.append({"category": category, "pages": list(items)})
    return groups


class DocsListView(TemplateView):
    """Redirect to the first available doc, or show an empty-state page."""

    template_name = "docs/list.html"

    def get(self, request, *args, **kwargs):
        first = DocPage.objects.order_by("category", "order", "title").first()
        if first:
            return redirect(first.get_absolute_url())
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["sidebar_groups"] = _get_sidebar_groups()
        return ctx


class DocDetailView(TemplateView):
    """Render a single DocPage, converting its Markdown content to HTML."""

    template_name = "docs/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page = get_object_or_404(DocPage, slug=kwargs["slug"])
        ctx["page"]           = page
        ctx["content_html"]   = _render_markdown(page.content_markdown)
        ctx["sidebar_groups"] = _get_sidebar_groups()
        return ctx
