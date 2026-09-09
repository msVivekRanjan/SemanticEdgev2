"""
nvr/models.py
-------------
Camera and Edge AI Services Data Models:
1. Camera: Represents a registered video source.
2. DetectionEvent: Persists detected objects with single snapshot evidence per object.
3. FaceReference: Uploaded reference biometric face profiles for student/staff attendance.
4. AttendanceRecord: Time-stamped face matching attendance log.
5. ObjectCountRecord: Factory line-crossing count log.
"""

from django.contrib.auth.models import User
from django.db import models


class Camera(models.Model):
    """A registered video source (webcam index or RTSP URL)."""

    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cameras",
    )
    name = models.CharField(
        max_length=100,
        help_text="Human-readable name, e.g. 'Front Door' or 'Main Road Intersection'.",
    )
    source_url = models.CharField(
        max_length=500,
        help_text="Video source: webcam index (e.g. '0') or full RTSP URL.",
    )
    tracker_enabled = models.BooleanField(
        default=True,
        help_text="Enable ByteTrack multi-object tracking. Disable for detection-only mode.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive cameras are excluded from the dashboard.",
    )
    night_threshold = models.FloatField(
        default=60.0,
        help_text="Grayscale mean intensity threshold below which scene is classified as Night Mode.",
    )
    scene_mode = models.CharField(
        max_length=10,
        default="day",
        choices=[("day", "Day Mode"), ("night", "Night Mode")],
        help_text="Current detected or default scene mode.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Camera"
        verbose_name_plural = "Cameras"

    def __str__(self) -> str:
        return f"{self.name} (owner: {self.owner.username})"


class DetectionEvent(models.Model):
    """
    Stores one image and detection record per unique detected object (track_id).
    Strictly isolated per user/camera.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="detections",
    )
    camera = models.ForeignKey(
        Camera,
        on_delete=models.CASCADE,
        related_name="detections",
    )
    track_id = models.IntegerField(default=-1)
    class_name = models.CharField(max_length=64)
    confidence = models.FloatField(default=0.0)
    bbox_x1 = models.FloatField(default=0.0)
    bbox_y1 = models.FloatField(default=0.0)
    bbox_x2 = models.FloatField(default=0.0)
    bbox_y2 = models.FloatField(default=0.0)
    line_crossing_status = models.CharField(max_length=32, default="none")
    frame_number = models.IntegerField(default=0)
    snapshot_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Relative media path to the saved object snapshot.",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Natural-language description for Qwen-VL or manual annotation.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Detection Event"
        verbose_name_plural = "Detection Events"

    def __str__(self) -> str:
        return f"{self.class_name} #{self.track_id} on {self.camera.name} ({self.created_at:%H:%M:%S})"


class FaceReference(models.Model):
    """
    Uploaded face reference photo for college / enterprise attendance marking.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="face_references",
    )
    person_name = models.CharField(max_length=150, verbose_name="Full Name")
    person_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Student / Employee ID",
        help_text="e.g. STU-2024-042 or EMP-1092",
    )
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Department / Class Section",
        help_text="e.g. Computer Science - Year 3",
    )
    photo = models.ImageField(
        upload_to="faces/references/",
        blank=True,
        null=True,
        verbose_name="Reference Face Image",
    )
    photo_path = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["person_name"]
        verbose_name = "Face Reference"
        verbose_name_plural = "Face References"

    def __str__(self) -> str:
        return f"{self.person_name} ({self.person_id or 'No ID'}) - {self.user.username}"


class AttendanceRecord(models.Model):
    """
    Biometric attendance log entry generated from live face matching.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    camera = models.ForeignKey(
        Camera,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    face_reference = models.ForeignKey(
        FaceReference,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    confidence = models.FloatField(default=0.92)
    status = models.CharField(max_length=30, default="Present")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"

    def __str__(self) -> str:
        return f"{self.face_reference.person_name} - {self.status} at {self.timestamp:%Y-%m-%d %H:%M:%S}"


class ObjectCountRecord(models.Model):
    """
    Real-time industrial conveyor and item counting log.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="count_records",
    )
    camera = models.ForeignKey(
        Camera,
        on_delete=models.CASCADE,
        related_name="count_records",
    )
    item_type = models.CharField(max_length=100, default="Manufactured Unit")
    total_count = models.IntegerField(default=0)
    in_count = models.IntegerField(default=0)
    out_count = models.IntegerField(default=0)
    rate_per_minute = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Object Count Record"
        verbose_name_plural = "Object Count Records"

    def __str__(self) -> str:
        return f"{self.item_type}: {self.total_count} units ({self.camera.name})"


class MonitoringZone(models.Model):
    """
    Dynamic monitoring zone or tripwire line defined by users directly on the camera feed.
    Coordinates are stored as normalized [[x, y], ...] points (values between 0.0 and 1.0)
    so they map correctly across various video and display resolutions.
    """

    ZONE_TYPE_CHOICES = [
        ("polygon", "Restricted Area (Polygon)"),
        ("line", "Tripwire (Line Crossing)"),
    ]

    camera = models.ForeignKey(
        Camera,
        on_delete=models.CASCADE,
        related_name="monitoring_zones",
    )
    name = models.CharField(
        max_length=100,
        default="Restricted Zone 1",
        help_text="User-defined zone label, e.g. 'Warehouse Gate' or 'Perimeter Fence'.",
    )
    zone_type = models.CharField(
        max_length=20,
        choices=ZONE_TYPE_CHOICES,
        default="polygon",
    )
    coordinates = models.JSONField(
        default=list,
        help_text="List of normalized points [[x, y], ...] representing polygon vertices or line endpoints.",
    )
    target_classes = models.JSONField(
        default=list,
        blank=True,
        help_text="List of target classes to monitor (e.g. ['person']). Empty implies all classes.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether intrusion detection is currently active for this zone.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Monitoring Zone"
        verbose_name_plural = "Monitoring Zones"

    def __str__(self) -> str:
        return f"{self.name} ({self.zone_type}) on {self.camera.name}"


class TelegramSession(models.Model):
    """
    Tracks authenticated session and interaction state for a Telegram user/chat.
    """

    STATE_CHOICES = [
        ("IDLE", "Idle / Not Started"),
        ("AWAITING_USERNAME", "Awaiting Username"),
        ("AWAITING_PASSWORD", "Awaiting Password"),
        ("AUTHENTICATED_IDLE", "Authenticated & Ready"),
        ("AWAITING_FEEDBACK", "Awaiting Feedback"),
    ]

    chat_id = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="telegram_sessions",
    )
    is_authenticated = models.BooleanField(default=False)
    state = models.CharField(max_length=32, choices=STATE_CHOICES, default="IDLE")
    pending_username = models.CharField(max_length=150, blank=True)
    last_intent = models.CharField(max_length=64, blank=True)
    last_query = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_interaction = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-last_interaction"]
        verbose_name = "Telegram Session"
        verbose_name_plural = "Telegram Sessions"

    def __str__(self) -> str:
        user_str = self.user.username if self.user else "Anonymous"
        status = "Authenticated" if self.is_authenticated else "Unauthenticated"
        return f"Chat {self.chat_id} ({user_str} - {status})"


class TelegramFeedback(models.Model):
    """
    Stores user feedback (Yes/No helpfulness) after the assistant serves a request.
    """

    session = models.ForeignKey(
        TelegramSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedbacks",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="telegram_feedbacks",
    )
    chat_id = models.CharField(max_length=64, db_index=True)
    query_text = models.TextField(blank=True)
    intent = models.CharField(max_length=64, blank=True)
    is_helpful = models.BooleanField(help_text="True if Yes, False if No")
    raw_feedback = models.CharField(max_length=20, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Telegram Feedback"
        verbose_name_plural = "Telegram Feedback Entries"

    def __str__(self) -> str:
        status = "Helpful" if self.is_helpful else "Unhelpful"
        return f"Feedback ({status}) from Chat {self.chat_id} for '{self.intent}'"
