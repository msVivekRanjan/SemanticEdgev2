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


class AlertConversation(models.Model):
    """
    Persistent investigation conversation associated with an alert, detection event,
    or object tracking session. Retains camera, detection, track, and timestamp context.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="alert_conversations",
    )
    event = models.ForeignKey(
        DetectionEvent,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
    )
    camera = models.ForeignKey(
        Camera,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conversations",
    )
    title = models.CharField(max_length=200, default="Alert Investigation")
    context_snapshot = models.JSONField(
        default=dict,
        blank=True,
        help_text="Snapshot of the alert context (camera, track, object class, timestamp).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        verbose_name = "Alert Conversation"
        verbose_name_plural = "Alert Conversations"

    def __str__(self) -> str:
        return f"Conversation #{self.id}: {self.title} ({self.user.username})"

    def get_context_summary(self) -> dict:
        """Returns structured dictionary of the conversation's active surveillance context."""
        ctx = dict(self.context_snapshot or {})
        if self.event:
            ctx.setdefault("event_id", self.event.id)
            ctx.setdefault("track_id", self.event.track_id)
            ctx.setdefault("class_name", self.event.class_name)
            ctx.setdefault("confidence", self.event.confidence)
            ctx.setdefault("camera_id", self.event.camera_id)
            ctx.setdefault("camera_name", self.event.camera.name)
            ctx.setdefault("status", self.event.line_crossing_status)
            ctx.setdefault("snapshot_url", self.event.snapshot_path)
            ctx.setdefault("timestamp", self.event.created_at.strftime("%Y-%m-%d %H:%M:%S"))
        elif self.camera:
            ctx.setdefault("camera_id", self.camera.id)
            ctx.setdefault("camera_name", self.camera.name)
        return ctx


class ChatMessage(models.Model):
    """
    Message in an alert/event investigation conversation.
    Stores user queries, system prompts, assistant responses, and structured evidence payloads.
    """

    SENDER_CHOICES = [
        ("user", "Operator"),
        ("assistant", "SemanticEdge Assistant"),
        ("system", "System"),
    ]

    conversation = models.ForeignKey(
        AlertConversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.CharField(max_length=20, choices=SENDER_CHOICES, default="user")
    content = models.TextField()
    evidence = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured evidence metadata, snapshots, tool outputs, or action links.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Chat Message"
        verbose_name_plural = "Chat Messages"

    def __str__(self) -> str:
        return f"[{self.sender.upper()}] Conv #{self.conversation_id}: {self.content[:40]}"

