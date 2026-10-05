"""
core/models.py
--------------
Demo inquiries and service acquisition lead management.
"""

from django.db import models


class DemoRequest(models.Model):
    """
    Stores Support & Contact inquiries and project deployment requests.
    """

    QUERY_TYPE_CHOICES = [
        ("technical_support", "Technical Support"),
        ("project_deployment", "Project / Deployment Query"),
        ("documentation", "Documentation & General Questions"),
        ("other", "Other Inquiry"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending Review"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    full_name = models.CharField(max_length=150, verbose_name="Full Name")
    company_name = models.CharField(
        max_length=200,
        blank=True,
        default="",
        verbose_name="Organization",
        help_text="Organization name (optional).",
    )
    email = models.EmailField(verbose_name="Email Address")
    query_type = models.CharField(
        max_length=50,
        choices=QUERY_TYPE_CHOICES,
        default="technical_support",
        verbose_name="Subject / Query Type",
    )
    message = models.TextField(
        verbose_name="Message",
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name="Status",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Support Inquiry"
        verbose_name_plural = "Support Inquiries"

    def __str__(self) -> str:
        org = f" ({self.company_name})" if self.company_name else ""
        return f"[{self.get_query_type_display()}] {self.full_name}{org} - {self.status}"
