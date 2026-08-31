"""
core/models.py
--------------
Demo inquiries and service acquisition lead management.
"""

from django.db import models


class DemoRequest(models.Model):
    """
    Stores 'Book a Demo' and service request submissions from clients.
    """

    CAMERA_COUNT_CHOICES = [
        ("1-5", "1 - 5 Cameras"),
        ("6-20", "6 - 20 Cameras"),
        ("21-50", "21 - 50 Cameras"),
        ("50+", "50+ Enterprise Cameras"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("contacted", "Contacted"),
        ("approved", "Approved / Activated"),
        ("closed", "Closed"),
    ]

    full_name = models.CharField(max_length=150, verbose_name="Full Name")
    company_name = models.CharField(
        max_length=200,
        verbose_name="Company / Institution Name",
        help_text="Organization name (e.g. City Traffic Authority, University, Manufacturing Plant).",
    )
    email = models.EmailField(verbose_name="Work Email")
    phone = models.CharField(max_length=50, blank=True, verbose_name="Phone Number")

    # Services interested in
    service_vehicles_people = models.BooleanField(
        default=False,
        verbose_name="Vehicles & People Detection (Traffic/Roads)",
    )
    service_face_recognition = models.BooleanField(
        default=False,
        verbose_name="Face Recognition & Attendance (Institutions)",
    )
    service_object_count = models.BooleanField(
        default=False,
        verbose_name="Industrial Object Counter (Factories)",
    )

    camera_count = models.CharField(
        max_length=50,
        choices=CAMERA_COUNT_CHOICES,
        default="1-5",
        verbose_name="Estimated Camera Count",
    )
    message = models.TextField(
        blank=True,
        verbose_name="Project Notes / Use Case Details",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Lead Status",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Demo Request"
        verbose_name_plural = "Demo Requests"

    def __str__(self) -> str:
        return f"Demo for {self.company_name} ({self.full_name}) - {self.status}"
