"""nvr/tests.py"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import (
    Camera,
    DetectionEvent,
    ObjectCountRecord,
    MonitoringZone,
    AlertConversation,
    ChatMessage,
)


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
        for url_name in ["nvr:dashboard", "nvr:live", "nvr:review", "nvr:explore", "nvr:export", "nvr:settings", "nvr:object_counter"]:
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
        self.assertContains(response2, "Object Tracker &amp; Restricted Area Monitoring")
        self.assertContains(response2, "Configured Zones")

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

    def test_review_datetime_and_description_search(self):
        self.client.login(username="alice", password="password123")
        event = DetectionEvent.objects.create(
            user=self.user1,
            camera=self.camera1,
            track_id=42,
            class_name="person",
            confidence=0.95,
            bbox_x1=10,
            bbox_y1=20,
            bbox_x2=80,
            bbox_y2=160,
            description="person in green shirt walking left",
            snapshot_path="/media/detections/user_alice/obj_42.jpg",
        )

        # Search by description keyword in Review
        res = self.client.get(reverse("nvr:review") + "?q=green+shirt")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "obj_42.jpg")

        # Search by class filter in Review
        res_class = self.client.get(reverse("nvr:review") + "?class=person")
        self.assertEqual(res_class.status_code, 200)
        self.assertContains(res_class, "obj_42.jpg")

        # Search by non-matching class in Review
        res_car = self.client.get(reverse("nvr:review") + "?class=car")
        self.assertEqual(res_car.status_code, 200)
        self.assertNotContains(res_car, "obj_42.jpg")

    def test_explore_investigation_workspace(self):
        self.client.login(username="alice", password="password123")
        res = self.client.get(reverse("nvr:explore"))
        self.assertEqual(res.status_code, 200)
        self.assertIn("conversations", res.context)
        self.assertIn("cameras", res.context)
        content = res.content.decode()
        self.assertIn("investigation-workspace", content)
        self.assertIn("threads-sidebar", content)
        self.assertIn("chat-workspace", content)

    def test_update_description_and_delete_detection_apis(self):
        self.client.login(username="alice", password="password123")
        event = DetectionEvent.objects.create(
            user=self.user1,
            camera=self.camera1,
            track_id=99,
            class_name="truck",
            confidence=0.91,
            bbox_x1=5,
            bbox_y1=5,
            bbox_x2=200,
            bbox_y2=150,
            snapshot_path="/media/detections/user_alice/obj_99.jpg",
        )

        # Update description API
        update_url = reverse("nvr:api_update_description", kwargs={"event_id": event.id})
        res_update = self.client.post(
            update_url,
            data={"description": "Delivery truck with blue container"},
            content_type="application/json",
        )
        self.assertEqual(res_update.status_code, 200)
        event.refresh_from_db()
        self.assertEqual(event.description, "Delivery truck with blue container")

        # Delete detection API
        delete_url = reverse("nvr:api_delete_detection", kwargs={"event_id": event.id})
        res_delete = self.client.post(delete_url)
        self.assertEqual(res_delete.status_code, 200)
        self.assertFalse(DetectionEvent.objects.filter(id=event.id).exists())

    def test_csv_log_export_endpoint(self):
        self.client.login(username="alice", password="password123")
        DetectionEvent.objects.create(
            user=self.user1,
            camera=self.camera1,
            track_id=7,
            class_name="bicycle",
            confidence=0.87,
            bbox_x1=10,
            bbox_y1=20,
            bbox_x2=50,
            bbox_y2=60,
            description="Red road bike",
        )
        res = self.client.get(reverse("nvr:export_csv"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "text/csv")
        self.assertIn("bicycle", res.content.decode())
        self.assertIn("Red road bike", res.content.decode())

    def test_monitoring_zone_apis(self):
        self.client.login(username="alice", password="password123")
        zones_url = reverse("nvr:camera_zones", kwargs={"camera_id": self.camera1.id})

        # Save new zone
        payload = {
            "zones": [
                {
                    "name": "Loading Bay Perimeter",
                    "zone_type": "polygon",
                    "coordinates": [[0.1, 0.1], [0.5, 0.1], [0.5, 0.5], [0.1, 0.5]],
                    "target_classes": ["person"],
                    "is_active": True,
                },
                {
                    "name": "North Gate Tripwire",
                    "zone_type": "line",
                    "coordinates": [[0.0, 0.4], [1.0, 0.4]],
                    "target_classes": [],
                    "is_active": True,
                },
            ]
        }
        res_post = self.client.post(zones_url, data=payload, content_type="application/json")
        self.assertEqual(res_post.status_code, 200)
        data = res_post.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 2)

        # GET zones
        res_get = self.client.get(zones_url)
        self.assertEqual(res_get.status_code, 200)
        get_data = res_get.json()
        self.assertEqual(len(get_data["zones"]), 2)
        self.assertEqual(get_data["zones"][0]["name"], "Loading Bay Perimeter")

    def test_day_night_threshold_api_and_computation(self):
        import numpy as np
        from .streaming import compute_day_night_scene

        self.client.login(username="alice", password="password123")
        thresh_url = reverse("nvr:camera_night_threshold", kwargs={"camera_id": self.camera1.id})
        res = self.client.post(thresh_url, data={"night_threshold": 75.5}, content_type="application/json")
        self.assertEqual(res.status_code, 200)
        self.camera1.refresh_from_db()
        self.assertEqual(self.camera1.night_threshold, 75.5)

        # Unit test compute_day_night_scene with bright frame
        bright_frame = np.full((100, 100, 3), 180, dtype=np.uint8)
        mode, intensity, night_cnt, day_cnt = compute_day_night_scene(
            bright_frame, smoothed_intensity=0.0, consecutive_night_frames=0, consecutive_day_frames=0,
            current_mode="day", threshold=75.5
        )
        self.assertEqual(mode, "day")
        self.assertGreater(intensity, 75.5)

        # Unit test compute_day_night_scene with dark frame
        dark_frame = np.full((100, 100, 3), 20, dtype=np.uint8)
        mode, intensity, night_cnt, day_cnt = compute_day_night_scene(
            dark_frame, smoothed_intensity=0.0, consecutive_night_frames=12, consecutive_day_frames=0,
            current_mode="day", threshold=75.5
        )
        self.assertEqual(mode, "night")
        self.assertLess(intensity, 75.5)

    def test_assistant_nlp_intent_parsing(self):
        from .assistant.nlp import AssistantNLPEngine

        nlp = AssistantNLPEngine()

        # 1. Latest intrusion
        intent, params = nlp.parse_intent("latest intrusion")
        self.assertEqual(intent, AssistantNLPEngine.INTENT_LATEST_INTRUSION)

        # 2. Show latest image
        intent, params = nlp.parse_intent("show latest image")
        self.assertEqual(intent, AssistantNLPEngine.INTENT_LATEST_IMAGE)

        # 3. Send image for Track ID 5
        intent, params = nlp.parse_intent("send image for Track ID 5")
        self.assertEqual(intent, AssistantNLPEngine.INTENT_TRACK_ID)
        self.assertEqual(params.get("track_id"), 5)

        # 4. Show yesterday's alerts
        intent, params = nlp.parse_intent("show yesterday's alerts")
        self.assertEqual(intent, AssistantNLPEngine.INTENT_YESTERDAY_ALERTS)

        # 5. Help
        intent, params = nlp.parse_intent("help")
        self.assertEqual(intent, AssistantNLPEngine.INTENT_HELP)

        # 6. General conversation
        intent, params = nlp.parse_intent("how are you today?")
        self.assertEqual(intent, AssistantNLPEngine.INTENT_GENERAL)

        intent, params = nlp.parse_intent("tell me a joke")
        self.assertEqual(intent, AssistantNLPEngine.INTENT_GENERAL)

    def test_assistant_controlled_nvr_tools(self):
        from .assistant.tools import NVRTools

        # Create monitoring zone
        MonitoringZone.objects.create(
            camera=self.camera1,
            name="Main Perimeter Zone",
            zone_type="polygon",
            target_classes=["person"],
            is_active=True,
        )

        # Create intrusion detection event
        event1 = DetectionEvent.objects.create(
            user=self.user1,
            camera=self.camera1,
            track_id=5,
            class_name="person",
            confidence=0.95,
            bbox_x1=50,
            bbox_y1=50,
            bbox_x2=200,
            bbox_y2=350,
            line_crossing_status="Intrusion: Main Perimeter",
            description="Person breached main perimeter",
            snapshot_path="/media/detections/test_snap.jpg",
        )

        # 1. Alert details
        details = NVRTools.get_alert_details(event1.id, user=self.user1)
        self.assertTrue(details["found"])
        self.assertEqual(details["track_id"], 5)
        self.assertEqual(details["class_name"], "person")
        self.assertEqual(details["camera_name"], "Alice Camera")

        # 2. Latest intrusion
        intrusion = NVRTools.get_latest_intrusion(user=self.user1)
        self.assertTrue(intrusion["found"])
        self.assertEqual(intrusion["id"], event1.id)

        # 3. Track history
        track_hist = NVRTools.get_track_history(5, user=self.user1)
        self.assertTrue(track_hist["found"])
        self.assertEqual(track_hist["total_records"], 1)

        # 4. Camera status
        cam_status = NVRTools.get_camera_status(user=self.user1)
        self.assertEqual(cam_status["total_cameras"], 1)
        self.assertEqual(cam_status["cameras"][0]["name"], "Alice Camera")

        # 5. System telemetry
        telemetry = NVRTools.get_system_telemetry(user=self.user1)
        self.assertEqual(telemetry["server_status"], "ONLINE (HEALTHY)")
        self.assertIn("detection_events_logged", telemetry)

        # 6. Detection statistics
        stats = NVRTools.get_detection_statistics("today", user=self.user1)
        self.assertGreaterEqual(stats["total_events"], 1)
        self.assertIn("person", stats["class_breakdown"])

        # 7. Monitoring zones
        zones = NVRTools.get_monitoring_zones(user=self.user1)
        self.assertEqual(zones["total_zones"], 1)

        # 8. Export records
        exports = NVRTools.get_export_records(user=self.user1)
        self.assertIn("total_files", exports)

    def test_assistant_service_conversation_lifecycle_and_persistence(self):
        from .assistant.service import AssistantService

        event = DetectionEvent.objects.create(
            user=self.user1,
            camera=self.camera1,
            track_id=88,
            class_name="car",
            confidence=0.91,
            bbox_x1=10,
            bbox_y1=10,
            bbox_x2=100,
            bbox_y2=100,
            line_crossing_status="Intrusion: Perimeter",
            description="Car in restricted lane",
            snapshot_path="/media/detections/car_88.jpg",
        )

        service = AssistantService()

        # 1. Create conversation bound to the alert
        conv = service.get_or_create_conversation(self.user1, event_id=event.id)
        self.assertIsNotNone(conv)
        self.assertEqual(conv.event, event)
        self.assertEqual(conv.camera, self.camera1)
        self.assertIn("Car", conv.title)
        self.assertEqual(conv.context_snapshot["track_id"], 88)

        # Verify initial system greeting
        first_msg = conv.messages.first()
        self.assertIsNotNone(first_msg)
        self.assertEqual(first_msg.sender, "system")
        self.assertIn("Car #88", first_msg.content)

        # 2. Operator asks question about snapshot without needing to re-explain the alert
        res = service.post_user_message(conv.id, self.user1, "show snapshot for this event")
        self.assertTrue(res["success"])
        self.assertIn("car_88.jpg", res["assistant_message"]["evidence"]["snapshot_url"])

        # 3. Multi-turn follow-up: Operator asks for track history
        res2 = service.post_user_message(conv.id, self.user1, "what is the movement history for this track?")
        self.assertTrue(res2["success"])
        self.assertIn("TRACK HISTORY RECORD", res2["assistant_message"]["content"])
        self.assertIn("#88", res2["assistant_message"]["content"])

        # Verify chat messages persisted in DB
        self.assertEqual(conv.messages.count(), 5)  # system + user1 + assistant1 + user2 + assistant2

    def test_assistant_conversations_api(self):
        from .assistant.service import AssistantService

        event = DetectionEvent.objects.create(
            user=self.user1,
            camera=self.camera1,
            track_id=42,
            class_name="truck",
            confidence=0.89,
            line_crossing_status="none",
        )

        self.client.login(username="alice", password="password123")

        # 1. Create conversation via API
        res_create = self.client.post(
            reverse("nvr:assistant_conversations"),
            data={"event_id": event.id},
            content_type="application/json",
        )
        self.assertEqual(res_create.status_code, 200)
        data_create = res_create.json()
        self.assertTrue(data_create["success"])
        conv_id = data_create["conversation"]["id"]

        # 2. Get conversation detail via API
        res_detail = self.client.get(
            reverse("nvr:assistant_conversation_detail", kwargs={"conversation_id": conv_id})
        )
        self.assertEqual(res_detail.status_code, 200)
        data_detail = res_detail.json()
        self.assertTrue(data_detail["success"])
        self.assertEqual(data_detail["conversation"]["context"]["track_id"], 42)

        # 3. Post user message via API
        res_msg = self.client.post(
            reverse("nvr:assistant_messages", kwargs={"conversation_id": conv_id}),
            data={"message": "camera status"},
            content_type="application/json",
        )
        self.assertEqual(res_msg.status_code, 200)
        data_msg = res_msg.json()
        self.assertTrue(data_msg["success"])
        self.assertIn("CAMERA FLEET STATUS", data_msg["assistant_message"]["content"])

        # 4. List conversations
        res_list = self.client.get(reverse("nvr:assistant_conversations"))
        self.assertEqual(res_list.status_code, 200)
        data_list = res_list.json()
        self.assertTrue(data_list["success"])
        self.assertGreaterEqual(len(data_list["conversations"]), 1)

    def test_no_emojis_in_all_reports(self):
        from .assistant.llm import RuleBasedNVRProvider
        import re

        provider = RuleBasedNVRProvider()
        emoji_pattern = re.compile(
            r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]"
        )

        for query in [
            "latest intrusion",
            "camera status",
            "system status",
            "detection statistics",
            "monitoring zones",
            "export requests",
            "help",
            "tell me something random",
        ]:
            res = provider.generate_response(query, history=[], context={}, user=self.user1)
            msg = res["content"]
            self.assertFalse(
                bool(emoji_pattern.search(msg)),
                f"Emoji detected in response for '{query}':\n{msg}",
            )

    def test_standalone_login_screen(self):
        res = self.client.get(reverse("accounts:login"))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode()
        self.assertIn("Sign In to NVR", content)
        self.assertIn("auth-card", content)
        # Verify website navbar and website footer are not present
        self.assertNotIn('class="navbar"', content)
        self.assertNotIn('class="footer"', content)

    def test_export_evidence_page_video_preview(self):
        self.client.login(username="alice", password="password123")
        res = self.client.get(reverse("nvr:export"))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode()
        self.assertIn("Annotated Video Preview", content)
        self.assertIn("evidence-video-player", content)

    def test_explore_view_live_logs_navigation(self):
        self.client.login(username="alice", password="password123")
        res = self.client.get(reverse("nvr:explore"))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode()
        self.assertIn("View Live Logs", content)
        self.assertIn(reverse("nvr:logs"), content)

    def test_settings_page_assistant_card(self):
        self.client.login(username="alice", password="password123")
        res = self.client.get(reverse("nvr:settings"))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode()
        self.assertIn("Internal Assistant Service", content)
        self.assertIn("btn-test-assistant", content)

    def test_assistant_diagnostics_api(self):
        self.client.login(username="alice", password="password123")
        res = self.client.get(reverse("nvr:assistant_diagnostics"))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertTrue(data["diagnostics"]["real_time_loop_decoupled"])
        self.assertIn("get_alert_details", data["diagnostics"]["tools_registered"])

    def test_explore_to_review_semantic_flow(self):
        event = DetectionEvent.objects.create(
            user=self.user1,
            camera=self.camera1,
            track_id=99,
            class_name="motorcycle",
            confidence=0.87,
            line_crossing_status="none",
        )
        self.client.login(username="alice", password="password123")

        # Test querying Review with specific track_id and event_id from Explore
        res = self.client.get(reverse("nvr:review") + f"?track_id=99&event_id={event.id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["selected_track_id"], "99")
        self.assertEqual(res.context["selected_event_id"], str(event.id))
        self.assertEqual(len(res.context["tracked_objects"]), 1)
        self.assertEqual(res.context["tracked_objects"][0]["track_id"], "99")
        self.assertEqual(res.context["tracked_objects"][0]["latest_event_id"], event.id)
        self.assertEqual(len(res.context["events"]), 1)
        self.assertEqual(res.context["events"][0]["track_id"], "99")



