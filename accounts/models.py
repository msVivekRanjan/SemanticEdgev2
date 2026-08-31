"""
accounts/models.py
------------------
User service subscription profile and entitlement management.
"""

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserServiceProfile(models.Model):
    """
    Stores purchased / allowed services for each user.
    Admin can toggle access to specific edge AI modules.
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="service_profile",
    )
    has_vehicles_people = models.BooleanField(
        default=True,
        verbose_name="Vehicles & People Detection",
        help_text="Enables YOLOv8 + ByteTrack vehicle and pedestrian detection for traffic/road monitoring.",
    )
    has_face_recognition = models.BooleanField(
        default=False,
        verbose_name="Face Recognition & Attendance",
        help_text="Enables face matching against uploaded reference images for colleges/institutions.",
    )
    has_object_count = models.BooleanField(
        default=False,
        verbose_name="Industrial Object Counter",
        help_text="Enables production line & conveyor belt item counting for factories.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Service Profile"
        verbose_name_plural = "User Service Profiles"

    def __str__(self) -> str:
        return f"Services for {self.user.username}"

    def can_access(self, service_key: str) -> bool:
        """Check if user has access to a specific service. Superusers have universal access."""
        if self.user.is_superuser:
            return True
        if service_key in ("vehicles_people", "live"):
            return self.has_vehicles_people
        if service_key == "face_recognition":
            return self.has_face_recognition
        if service_key == "object_count":
            return self.has_object_count
        return False


@receiver(post_save, sender=User)
def create_or_update_user_service_profile(sender, instance, created, **kwargs):
    """Ensure every user automatically has a UserServiceProfile."""
    if created:
        UserServiceProfile.objects.create(user=instance)
    else:
        if not hasattr(instance, "service_profile"):
            UserServiceProfile.objects.create(user=instance)
