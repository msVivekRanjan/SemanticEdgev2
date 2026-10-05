"""core/tests.py"""

from django.test import TestCase
from django.urls import reverse
from .models import DemoRequest


class CoreViewTests(TestCase):
    def test_home_page_status(self):
        url = reverse("core:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        self.assertContains(response, "SemanticEdge")
        self.assertContains(response, "Core Architecture")
        self.assertContains(response, "Reduce false positives")
        self.assertContains(response, "Persistent identity")
        self.assertContains(response, "Structured event log")

    def test_support_contact_page_renders(self):
        url = reverse("core:book_demo") + "?topic=technical"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/book_demo.html")
        self.assertContains(response, "How can we")
        self.assertContains(response, "help?")
        self.assertContains(response, "Technical Support")
        self.assertContains(response, "Project / Deployment Queries")
        self.assertContains(response, "Documentation &amp; General Questions")
        self.assertContains(response, "Send Message")

    def test_support_contact_submission_success(self):
        post_data = {
            "full_name": "Dr. Aris Thorne",
            "company_name": "Apex Research Labs",
            "email": "thorne@apex.org",
            "query_type": "technical_support",
            "message": "Need guidance on optimizing YOLOv8 inference latency on Apple Silicon MPS.",
        }
        response = self.client.post(reverse("core:book_demo"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Message Received!")

        # Verify DB entry
        req = DemoRequest.objects.get(email="thorne@apex.org")
        self.assertEqual(req.full_name, "Dr. Aris Thorne")
        self.assertEqual(req.company_name, "Apex Research Labs")
        self.assertEqual(req.query_type, "technical_support")
        self.assertEqual(req.status, "pending")

    def test_support_contact_submission_optional_organization(self):
        post_data = {
            "full_name": "Jane Doe",
            "company_name": "",
            "email": "jane@example.com",
            "query_type": "documentation",
            "message": "Question regarding Tailscale RTSP streaming configuration.",
        }
        response = self.client.post(reverse("core:book_demo"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Message Received!")

        req = DemoRequest.objects.get(email="jane@example.com")
        self.assertEqual(req.full_name, "Jane Doe")
        self.assertEqual(req.company_name, "")
        self.assertEqual(req.query_type, "documentation")
