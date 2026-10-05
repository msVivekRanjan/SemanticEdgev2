"""
core/admin.py
-------------
Django admin registration for Demo Requests.
"""

from django.contrib import admin
from .models import DemoRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "company_name",
        "email",
        "query_type",
        "status",
        "created_at",
    )
    list_filter = ("status", "query_type", "created_at")
    search_fields = ("full_name", "company_name", "email", "message")
    list_editable = ("status",)
