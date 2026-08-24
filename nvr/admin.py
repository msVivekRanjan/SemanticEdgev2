"""nvr/admin.py"""

from django.contrib import admin
from .models import Camera


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display  = ("name", "owner", "source_url", "tracker_enabled", "is_active", "created_at")
    list_filter   = ("is_active", "tracker_enabled", "owner")
    search_fields = ("name", "owner__username")
    ordering      = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Identity", {
            "fields": ("owner", "name"),
        }),
        ("Source", {
            "fields": ("source_url",),
            "description": "⚠️  RTSP URLs with embedded credentials are stored as plaintext in v1.",
        }),
        ("Options", {
            "fields": ("tracker_enabled", "is_active"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
