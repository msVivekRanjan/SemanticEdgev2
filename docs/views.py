"""
docs/views.py
-------------
DocsListView            — redirects to the first doc page, or shows empty state.
DocDetailView           — renders a single DocPage with TOC & Prev/Next navigation.
DocMarkdownDownloadView — downloads the raw Markdown content as a .md file.
"""

from __future__ import annotations

import re
from itertools import groupby

import markdown2
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from django.views.generic import TemplateView

from .models import DocPage


def _render_markdown(raw: str) -> str:
    """Convert Markdown to HTML with syntax highlighting and automatic header IDs."""
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


def _extract_toc(content_html: str) -> list[dict]:
    """Extract h2 and h3 headings with their generated IDs for the Table of Contents."""
    pattern = re.compile(r'<h([23])\s+id="([^"]+)"[^>]*>(.*?)</h\1>', re.IGNORECASE | re.DOTALL)
    toc = []
    for match in pattern.finditer(content_html):
        level = int(match.group(1))
        heading_id = match.group(2)
        # Strip any nested HTML tags from heading text
        raw_text = re.sub(r'<[^>]+>', '', match.group(3)).strip()
        if raw_text:
            toc.append({
                "level": level,
                "id": heading_id,
                "text": raw_text,
            })
    return toc


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
    """Render a single DocPage, generating its TOC and Prev/Next page pointers."""

    template_name = "docs/detail.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page = get_object_or_404(DocPage, slug=kwargs["slug"])

        # Fetch all pages sorted by logical reading order
        all_pages = list(DocPage.objects.order_by("order", "category", "title"))
        try:
            idx = all_pages.index(page)
            prev_page = all_pages[idx - 1] if idx > 0 else None
            next_page = all_pages[idx + 1] if idx < len(all_pages) - 1 else None
        except ValueError:
            prev_page = None
            next_page = None

        content_html = _render_markdown(page.content_markdown)

        ctx["page"]           = page
        ctx["content_html"]   = content_html
        ctx["toc"]            = _extract_toc(content_html)
        ctx["prev_page"]      = prev_page
        ctx["next_page"]      = next_page
        ctx["sidebar_groups"] = _get_sidebar_groups()
        return ctx


class DocMarkdownDownloadView(View):
    """Serve the raw Markdown content as a downloadable .md file."""

    def get(self, request, slug: str, *args, **kwargs) -> HttpResponse:
        page = get_object_or_404(DocPage, slug=slug)
        filename = f"{page.slug}.md"
        response = HttpResponse(page.content_markdown, content_type="text/markdown; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
