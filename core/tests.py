"""core/tests.py"""

from django.test import TestCase
from django.urls import reverse


class CoreViewTests(TestCase):
    def test_home_page_status_and_template(self):
        url = reverse("core:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/home.html")
        self.assertTemplateUsed(response, "base.html")
        self.assertContains(response, "SemanticEdge")
        self.assertContains(response, "Locally processed")
