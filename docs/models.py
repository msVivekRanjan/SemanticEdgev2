"""
docs/models.py
--------------
DocPage: model-driven documentation pages.
Content is stored as raw Markdown and rendered to HTML at view time
using markdown2 + pygments for syntax highlighting.
"""

from django.db import models
from django.urls import reverse


class DocPage(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(
        unique=True,
        help_text="URL-safe identifier, e.g. 'getting-started'. Auto-populated from title."
    )
    content_markdown = models.TextField(
        blank=True,
        help_text="Paste or upload Markdown content here. Code fences with language tags are syntax-highlighted."
    )
    category = models.CharField(
        max_length=100,
        help_text="Group label shown in the sidebar, e.g. 'Getting Started', 'Configuration'."
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Sort order within the category. Lower numbers appear first."
    )
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "title"]
        verbose_name = "Documentation Page"
        verbose_name_plural = "Documentation Pages"

    def __str__(self) -> str:
        return f"[{self.category}] {self.title}"

    def get_absolute_url(self) -> str:
        return reverse("docs:detail", kwargs={"slug": self.slug})
