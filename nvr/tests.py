"""nvr/tests.py"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Camera


class NVRAuthorizationAndTabsTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="alice", password="password123")
        self.user2 = User.objects.create_user(username="bob", password="password123")

        self.camera1 = Camera.objects.create(
            owner=self.user1,
            name="Alice Camera",
            source_url="0",
            tracker_enabled=True,
        )
        self.camera2 = Camera.objects.create(
            owner=self.user2,
            name="Bob Camera",
            source_url="1",
            tracker_enabled=False,
        )

    def test_tabs_require_login(self):
        for url_name in ["nvr:dashboard", "nvr:live", "nvr:review", "nvr:explore", "nvr:export", "nvr:settings"]:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_live_tab_renders_for_logged_in_user(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(reverse("nvr:live"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nvr/live.html")
        self.assertContains(response, "Alice Camera")
        self.assertNotContains(response, "Bob Camera")

    def test_review_tab_renders_for_logged_in_user(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(reverse("nvr:review"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nvr/review.html")
        self.assertContains(response, "Event Review")

    def test_explore_tab_renders_for_logged_in_user(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(reverse("nvr:explore"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nvr/explore.html")
        self.assertContains(response, "Object Exploration")
        self.assertContains(response, "Persons")
        self.assertContains(response, "Cars")

    def test_export_tab_renders_for_logged_in_user(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(reverse("nvr:export"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nvr/export.html")
        self.assertContains(response, "Export Evidence")

    def test_settings_tab_renders_and_handles_add_camera(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(reverse("nvr:settings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nvr/settings.html")

        # Post to add camera
        post_res = self.client.post(reverse("nvr:settings"), {
            "action": "add_camera",
            "name": "Driveway Sensor",
            "source_url": "0",
            "tracker_enabled": "on",
        })
        self.assertEqual(post_res.status_code, 302)
        self.assertTrue(Camera.objects.filter(name="Driveway Sensor", owner=self.user1).exists())

    def test_user_cannot_access_other_users_stream(self):
        self.client.login(username="alice", password="password123")
        # Attempt to access Bob's camera stream & stats
        url_stream = reverse("nvr:stream", kwargs={"camera_id": self.camera2.id})
        res_stream = self.client.get(url_stream)
        self.assertEqual(res_stream.status_code, 403)

        url_stats = reverse("nvr:stats", kwargs={"camera_id": self.camera2.id})
        res_stats = self.client.get(url_stats)
        self.assertEqual(res_stats.status_code, 403)

    def test_system_status_api_endpoint(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(reverse("nvr:system_status"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("cpu_percent", data)
        self.assertIn("memory_percent", data)
        self.assertIn("device", data)
        self.assertIn("health", data)
        self.assertEqual(data["health"], "OPTIMAL")
