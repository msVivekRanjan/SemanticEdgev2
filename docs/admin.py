"""docs/admin.py — DocPage admin with Markdown textarea."""

from django.contrib import admin
from django import forms
from .models import DocPage


class DocPageAdminForm(forms.ModelForm):
    """Custom form with a tall Textarea for the Markdown content field."""

    content_markdown = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 40, "style": "font-family: monospace; font-size: 13px;"}),
        required=False,
        help_text="Paste Markdown here. Fenced code blocks (```python) are syntax-highlighted.",
    )

    class Meta:
        model = DocPage
        fields = "__all__"


@admin.register(DocPage)
class DocPageAdmin(admin.ModelAdmin):
    form = DocPageAdminForm

    list_display  = ("title", "category", "order", "slug", "updated_at")
    list_filter   = ("category",)
    search_fields = ("title", "slug", "category")
    ordering      = ("category", "order")

    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        ("Identity", {
            "fields": ("title", "slug", "category", "order"),
        }),
        ("Content", {
            "fields": ("content_markdown",),
            "description": "Supports full Markdown with GitHub-Flavored fenced code blocks.",
        }),
    )
