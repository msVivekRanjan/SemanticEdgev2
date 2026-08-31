"""nvr/tests.py"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Camera, DetectionEvent, FaceReference, AttendanceRecord, ObjectCountRecord


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
        for url_name in ["nvr:dashboard", "nvr:live", "nvr:review", "nvr:explore", "nvr:export", "nvr:settings", "nvr:face_recognition", "nvr:object_counter"]:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(response.url.startswith(reverse("accounts:login")))

    def test_live_tab_grid_renders_for_logged_in_user(self):
        self.client.login(username="alice", password="password123")
        response = self.client.get(reverse("nvr:live"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nvr/live.html")
        self.assertContains(response, "Alice Camera")
        self.assertContains(response, "Multi-Camera Live Grid")
        self.assertNotContains(response, "Bob Camera")

    def test_single_camera_focus_view_renders(self):
        self.client.login(username="alice", password="password123")
        url = reverse("nvr:camera_live", kwargs={"camera_id": self.camera1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nvr/live.html")
        self.assertContains(response, "Live AI Focus")
        self.assertContains(response, "All Cameras")
        self.assertContains(response, "Detection Logs")

    def test_camera_detection_log_view_renders_without_error(self):
        self.client.login(username="alice", password="password123")
        # Ensure log view for camera1 reverses and returns 200
        url = reverse("nvr:log", kwargs={"camera_id": self.camera1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "nvr/log.html")
        self.assertContains(response, "Detection &amp; Event Logs")
        self.assertContains(response, "Alice Camera")

    def test_single_snapshot_detection_event_persistence_and_user_isolation(self):
        # Create detection event for Alice
        DetectionEvent.objects.create(
            user=self.user1,
            camera=self.camera1,
            track_id=1,
            class_name="car",
            confidence=0.94,
            bbox_x1=10,
            bbox_y1=20,
            bbox_x2=100,
            bbox_y2=200,
            snapshot_path="/media/detections/user_alice/obj_1_car.jpg",
        )

        # Create detection event for Bob
        DetectionEvent.objects.create(
            user=self.user2,
            camera=self.camera2,
            track_id=2,
            class_name="person",
            confidence=0.88,
            bbox_x1=15,
            bbox_y1=25,
            bbox_x2=110,
            bbox_y2=210,
            snapshot_path="/media/detections/user_bob/obj_2_person.jpg",
        )

        self.client.login(username="alice", password="password123")
        review_res = self.client.get(reverse("nvr:review"))
        self.assertEqual(review_res.status_code, 200)
        self.assertContains(review_res, "car")
        self.assertNotContains(review_res, "/media/detections/user_bob/obj_2_person.jpg")

    def test_service_gating_face_recognition(self):
        self.client.login(username="alice", password="password123")
        # Alice does not have face_recognition service enabled by default
        response = self.client.get(reverse("nvr:face_recognition"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SERVICE NOT ACTIVATED")
        self.assertContains(response, "Book a Demo to Unlock")

        # Now admin enables face_recognition for Alice
        profile = self.user1.service_profile
        profile.has_face_recognition = True
        profile.save()

        response2 = self.client.get(reverse("nvr:face_recognition"))
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, "Register Reference Face")
        self.assertContains(response2, "Registered Faces")

    def test_service_gating_object_counter(self):
        self.client.login(username="alice", password="password123")
        # Object counter locked initially
        response = self.client.get(reverse("nvr:object_counter"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "SERVICE NOT ACTIVATED")

        # Unlock service
        profile = self.user1.service_profile
        profile.has_object_count = True
        profile.save()

        response2 = self.client.get(reverse("nvr:object_counter"))
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, "Industrial Object Counter")
        self.assertContains(response2, "Live Production Tally")

    def test_user_cannot_access_other_users_stream(self):
        self.client.login(username="alice", password="password123")
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
