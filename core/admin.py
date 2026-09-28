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
        "company_name",
        "full_name",
        "email",
        "phone",
        "service_vehicles_people",
        "service_object_count",
        "camera_count",
        "status",
        "created_at",
    )
    list_filter = ("status", "service_vehicles_people", "service_object_count", "camera_count")
    search_fields = ("company_name", "full_name", "email", "phone", "message")
    list_editable = ("status",)
