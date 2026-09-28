"""nvr/admin.py"""

from django.contrib import admin
from .models import Camera, DetectionEvent, ObjectCountRecord


@admin.register(ObjectCountRecord)
class ObjectCountRecordAdmin(admin.ModelAdmin):
    list_display = ("item_type", "total_count", "in_count", "out_count", "rate_per_minute", "camera", "user", "created_at")
    list_filter = ("item_type", "camera", "user")
    search_fields = ("item_type", "user__username")
