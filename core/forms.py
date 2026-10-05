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
            "query_type",
            "message",
        )
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "e.g. Alex Johnson",
                "required": True,
            }),
            "company_name": forms.TextInput(attrs={
                "class": "input",
                "placeholder": "e.g. Apex Security, City Labs (optional)",
            }),
            "email": forms.EmailInput(attrs={
                "class": "input",
                "placeholder": "alex@organization.com",
                "required": True,
            }),
            "query_type": forms.Select(attrs={
                "class": "nvr-select",
                "style": "width: 100%;",
            }),
            "message": forms.Textarea(attrs={
                "class": "input",
                "rows": 5,
                "placeholder": "How can we help? Describe your technical issue, deployment requirement, or question...",
                "required": True,
            }),
        }
