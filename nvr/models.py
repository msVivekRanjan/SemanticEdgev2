"""
nvr/models.py
-------------
Camera: represents a registered video source owned by a user.
"""

from django.contrib.auth.models import User
from django.db import models


class Camera(models.Model):
    """
    A registered video source (webcam index or RTSP URL).

    Security note
    -------------
    `source_url` may contain embedded RTSP credentials
    (e.g. rtsp://user:pass@host/stream). In v1, these are stored as-is in
    the database, which is acceptable for a local single-user deployment.

    v2 hardening: encrypt `source_url` at rest using django-encrypted-fields
    or store only a reference to an environment variable name here and resolve
    the actual URL from the environment at stream time.
    """

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cameras",
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable name, e.g. 'Front Door' or 'Parking Lot'.",
    )
    source_url = models.CharField(
        max_length=500,
        help_text=(
            "Video source: webcam index (e.g. '0') or full RTSP URL "
            "(e.g. 'rtsp://user:pass@192.168.1.100:554/stream'). "
            "WARNING: RTSP URLs with credentials are stored as-is in v1."
        ),
    )
    tracker_enabled = models.BooleanField(
        default=True,
        help_text="Enable ByteTrack multi-object tracking. Disable for detection-only mode.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive cameras are excluded from the dashboard.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Camera"
        verbose_name_plural = "Cameras"

    def __str__(self) -> str:
        return f"{self.name} (owner: {self.owner.username})"
