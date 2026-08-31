"""
core/forms.py
-------------
Contact and Book a Demo forms.
"""

from django import forms
from .models import DemoRequest


class DemoRequestForm(forms.ModelForm):
    class Meta:
        model = DemoRequest
        fields = (
            "full_name",
            "company_name",
            "email",
            "phone",
            "service_vehicles_people",
            "service_face_recognition",
            "service_object_count",
            "camera_count",
            "message",
        )
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "e.g. Dr. Rajesh Sharma / Jane Doe",
                "required": True,
            }),
            "company_name": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "e.g. Metropolitan Traffic Control / Apex Institute / Precision Gear Ltd",
                "required": True,
            }),
            "email": forms.EmailInput(attrs={
                "class": "input",
                "placeholder": "contact@organization.gov / admin@college.edu",
                "required": True,
            }),
            "phone": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "+1 (555) 000-0000 / +91 98765 43210",
            }),
            "service_vehicles_people": forms.CheckboxInput(attrs={"class": "custom-checkbox"}),
            "service_face_recognition": forms.CheckboxInput(attrs={"class": "custom-checkbox"}),
            "service_object_count": forms.CheckboxInput(attrs={"class": "custom-checkbox"}),
            "camera_count": forms.Select(attrs={"class": "nvr-select", "style": "width: 100%;"}),
            "message": forms.Textarea(attrs={
                "class": "input",
                "rows": 4,
                "placeholder": "Describe your deployment scale, hardware setup, or specific analytics needs...",
            }),
        }
