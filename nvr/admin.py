"""nvr/admin.py"""

from django.contrib import admin
from .models import AttendanceRecord, Camera, DetectionEvent, FaceReference, ObjectCountRecord


@admin.register(Camera)
class CameraAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "source_url", "tracker_enabled", "is_active", "created_at")
    list_filter = ("is_active", "tracker_enabled", "owner")
    search_fields = ("name", "owner__username")
    ordering = ("-created_at",)
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


@admin.register(DetectionEvent)
class DetectionEventAdmin(admin.ModelAdmin):
    list_display = ("class_name", "track_id", "confidence", "camera", "user", "description", "created_at", "snapshot_path")
    list_filter = ("class_name", "camera", "user")
    search_fields = ("class_name", "track_id", "description", "user__username")
    readonly_fields = ("created_at",)


@admin.register(FaceReference)
class FaceReferenceAdmin(admin.ModelAdmin):
    list_display = ("person_name", "person_id", "department", "user", "created_at")
    list_filter = ("department", "user")
    search_fields = ("person_name", "person_id", "department", "user__username")


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ("face_reference", "status", "confidence", "camera", "user", "timestamp")
    list_filter = ("status", "camera", "user")
    search_fields = ("face_reference__person_name", "user__username")


@admin.register(ObjectCountRecord)
class ObjectCountRecordAdmin(admin.ModelAdmin):
    list_display = ("item_type", "total_count", "in_count", "out_count", "rate_per_minute", "camera", "user", "created_at")
    list_filter = ("item_type", "camera", "user")
    search_fields = ("item_type", "user__username")
