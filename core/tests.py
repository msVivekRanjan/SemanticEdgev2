"""core/tests.py"""

from django.test import TestCase
from django.urls import reverse
from .models import DemoRequest


class CoreViewTests(TestCase):
    def test_home_page_status_and_catalogue(self):
        url = reverse("core:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        self.assertContains(response, "SemanticEdge")
        self.assertContains(response, "SERVICES CATALOGUE")
        self.assertContains(response, "Vehicles & People Detection")
        self.assertContains(response, "Restricted Area & Perimeter Security")
        self.assertContains(response, "Industrial Object Counter")

    def test_book_demo_page_renders_with_preselection(self):
        url = reverse("core:book_demo") + "?service=vehicles_people"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/book_demo.html")
        self.assertContains(response, "Book a Demo")
        self.assertContains(response, "Request Service Activation")

    def test_book_demo_submission_success(self):
        post_data = {
            "full_name": "Dr. Aris Thorne",
            "company_name": "National Traffic Authority",
            "email": "thorne@traffic.gov",
            "phone": "+1 555-0192",
            "service_vehicles_people": True,
            "camera_count": "21-50",
            "message": "Need multi-intersection speed and lane violation tracking.",
        }
        response = self.client.post(reverse("core:book_demo"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Demo Request Received!")

        # Verify DB entry
        req = DemoRequest.objects.get(email="thorne@traffic.gov")
        self.assertEqual(req.company_name, "National Traffic Authority")
        self.assertTrue(req.service_vehicles_people)
        self.assertEqual(req.status, "pending")
