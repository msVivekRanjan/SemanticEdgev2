"""nvr/tests.py"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import (
    Camera,
    DetectionEvent,
    FaceReference,
    AttendanceRecord,
    ObjectCountRecord,
    MonitoringZone,
    TelegramSession,
    TelegramFeedback,
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

    def test_explore_datetime_and_description_search(self):
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

        # Search by description keyword
        res = self.client.get(reverse("nvr:explore") + "?q=green+shirt")
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "obj_42.jpg")

        # Search by class filter
        res_class = self.client.get(reverse("nvr:explore") + "?class=person")
        self.assertEqual(res_class.status_code, 200)
        self.assertContains(res_class, "obj_42.jpg")

        # Search by non-matching class
        res_car = self.client.get(reverse("nvr:explore") + "?class=car")
        self.assertEqual(res_car.status_code, 200)
        self.assertNotContains(res_car, "obj_42.jpg")

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

    def test_openclaw_nlp_intent_parsing(self):
        from .openclaw import (
            OpenClawNLPEngine,
            INTENT_LATEST_INTRUSION,
            INTENT_LATEST_IMAGE,
            INTENT_TRACK_ID,
            INTENT_YESTERDAY_ALERTS,
            INTENT_HELP,
            INTENT_GENERAL_CONVERSATION,
        )

        nlp = OpenClawNLPEngine()

        # 1. Latest intrusion
        intent, params = nlp.parse_intent("latest intrusion")
        self.assertEqual(intent, INTENT_LATEST_INTRUSION)

        # 2. Show latest image
        intent, params = nlp.parse_intent("show latest image")
        self.assertEqual(intent, INTENT_LATEST_IMAGE)

        # 3. Send image for Track ID 5
        intent, params = nlp.parse_intent("send image for Track ID 5")
        self.assertEqual(intent, INTENT_TRACK_ID)
        self.assertEqual(params.get("track_id"), 5)

        # 4. Show yesterday's alerts
        intent, params = nlp.parse_intent("show yesterday's alerts")
        self.assertEqual(intent, INTENT_YESTERDAY_ALERTS)

        # 5. Help
        intent, params = nlp.parse_intent("help")
        self.assertEqual(intent, INTENT_HELP)

        # 6. General conversation (should be classified as general conversation and rejected)
        intent, params = nlp.parse_intent("how are you today?")
        self.assertEqual(intent, INTENT_GENERAL_CONVERSATION)

        intent, params = nlp.parse_intent("tell me a joke")
        self.assertEqual(intent, INTENT_GENERAL_CONVERSATION)

    def test_openclaw_natural_language_queries(self):
        from .openclaw import OpenClawAssistant
        from django.utils import timezone
        from datetime import timedelta

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
            line_crossing_status="Intrusion: Main Gate",
            description="Person breached main perimeter",
            snapshot_path="",
        )

        assistant = OpenClawAssistant(bot_token="dummy_test_token", chat_id="123456")

        # Query by Track ID 5
        res_track = assistant.interpret_and_query("send image for Track ID 5")
        self.assertTrue(res_track["success"])
        self.assertEqual(res_track["event"].track_id, 5)

        # Query latest intrusion
        res_intrusion = assistant.interpret_and_query("latest intrusion")
        self.assertTrue(res_intrusion["success"])
        self.assertEqual(res_intrusion["event"].track_id, 5)

        # Query latest image
        res_latest = assistant.interpret_and_query("show latest image")
        self.assertTrue(res_latest["success"])
        self.assertEqual(res_latest["event"].class_name, "person")

        # Query general conversation -> Must receive helpful suggestions (not rejection)
        res_gen = assistant.interpret_and_query("tell me a funny story")
        self.assertFalse(res_gen["success"])
        self.assertIn("QUERY NOT RECOGNIZED", res_gen["message"])
        self.assertIn("RECOMMENDED OPERATIONAL QUERIES", res_gen["message"])

    def test_openclaw_handle_incoming_message_stages(self):
        from .openclaw import OpenClawAssistant, send_telegram_alert
        from unittest.mock import patch

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
            snapshot_path="",
        )

        assistant = OpenClawAssistant(bot_token="dummy_test_token", chat_id="123456")

        # Authenticate session for chat 123456
        TelegramSession.objects.create(
            chat_id="123456",
            user=self.user1,
            is_authenticated=True,
            state="AUTHENTICATED_IDLE",
        )

        with patch.object(assistant, "send_text_response", return_value=True) as mock_send_text:
            # Test NVR query execution
            res = assistant.handle_incoming_message("send image for Track ID 88", chat_id="123456")
            self.assertTrue(res["success"])
            self.assertEqual(res["intent"], "track_id")
            mock_send_text.assert_called_once()

            # Test general conversation receiving helpful guidance
            mock_send_text.reset_mock()
            res_gen = assistant.handle_incoming_message("what is your favorite movie?", chat_id="123456")
            self.assertEqual(res_gen["intent"], "general_conversation")
            self.assertFalse(res_gen["success"])
            mock_send_text.assert_called_once()
            call_args = mock_send_text.call_args[0]
            self.assertIn("QUERY NOT RECOGNIZED", call_args[1])
            self.assertIn("RECOMMENDED OPERATIONAL QUERIES", call_args[1])

        # Test automatic intrusion alert dispatch
        alert_sent = send_telegram_alert(event)
        self.assertTrue(alert_sent)

    def test_telegram_auth_flow_interactive_and_direct(self):
        from .openclaw import OpenClawAssistant
        from unittest.mock import patch

        assistant = OpenClawAssistant(bot_token="dummy_test_token", chat_id="777888")

        with patch.object(assistant, "send_text_response", return_value=True) as mock_send:
            # 1. Unauthenticated /start triggers username prompt
            res = assistant.handle_incoming_message("/start", chat_id="777888")
            self.assertFalse(res["success"])
            self.assertIn("AUTHENTICATION REQUIRED", res["message"])

            # 2. Enter invalid username
            res = assistant.handle_incoming_message("nonexistent_user", chat_id="777888")
            self.assertFalse(res["success"])
            self.assertIn("not found in NVR database", res["message"])

            # 3. Enter valid username (alice) -> Prompts for password
            res = assistant.handle_incoming_message("alice", chat_id="777888")
            self.assertFalse(res["success"])
            self.assertIn("Please enter your password", res["message"])

            # 4. Enter incorrect password -> Fails
            res = assistant.handle_incoming_message("wrongpass", chat_id="777888")
            self.assertFalse(res["success"])
            self.assertIn("Invalid password", res["message"])

            # 5. Direct login /login alice password123 -> Authenticates session
            res = assistant.handle_incoming_message("/login alice password123", chat_id="777888")
            self.assertTrue(res["success"])
            self.assertIn("SESSION ESTABLISHED", res["message"])
            self.assertIn("CAPABILITIES & SAMPLE QUERIES", res["message"])

            # Verify session model in DB
            sess = TelegramSession.objects.get(chat_id="777888")
            self.assertTrue(sess.is_authenticated)
            self.assertEqual(sess.user, self.user1)

            # 6. /logout terminates session
            res_logout = assistant.handle_incoming_message("/logout", chat_id="777888")
            self.assertTrue(res_logout["success"])
            self.assertIn("SESSION TERMINATED", res_logout["message"])
            sess.refresh_from_db()
            self.assertFalse(sess.is_authenticated)

    def test_expanded_surveillance_intents(self):
        from .openclaw import OpenClawAssistant
        from unittest.mock import patch

        # Create monitoring zone
        MonitoringZone.objects.create(
            camera=self.camera1,
            name="Main Gate Zone",
            zone_type="line",
            target_classes=["person"],
            is_active=True,
        )

        # Create test event
        DetectionEvent.objects.create(
            user=self.user1,
            camera=self.camera1,
            track_id=10,
            class_name="person",
            confidence=0.92,
            line_crossing_status="Intrusion: Main Gate",
            description="Person breached zone",
        )

        assistant = OpenClawAssistant(bot_token="dummy_test_token", chat_id="999000")
        TelegramSession.objects.create(
            chat_id="999000",
            user=self.user1,
            is_authenticated=True,
            state="AUTHENTICATED_IDLE",
        )

        with patch.object(assistant, "send_text_response", return_value=True):
            # Camera status
            res_cam = assistant.handle_incoming_message("camera status", chat_id="999000")
            self.assertTrue(res_cam["success"])
            self.assertIn("CAMERA FLEET STATUS", res_cam["message"])

            # System status
            res_sys = assistant.handle_incoming_message("system status", chat_id="999000")
            self.assertTrue(res_sys["success"])
            self.assertIn("SYSTEM TELEMETRY", res_sys["message"])

            # Detection statistics
            res_stats = assistant.handle_incoming_message("detection statistics", chat_id="999000")
            self.assertTrue(res_stats["success"])
            self.assertIn("DETECTION STATISTICS", res_stats["message"])

            # Monitoring zones
            res_zones = assistant.handle_incoming_message("monitoring zones", chat_id="999000")
            self.assertTrue(res_zones["success"])
            self.assertIn("MONITORING ZONES", res_zones["message"])

            # Export requests
            res_exp = assistant.handle_incoming_message("export requests", chat_id="999000")
            self.assertTrue(res_exp["success"])
            self.assertIn("EXPORT ARCHIVE", res_exp["message"])

    def test_telegram_feedback_collection(self):
        from .openclaw import OpenClawAssistant
        from unittest.mock import patch

        assistant = OpenClawAssistant(bot_token="dummy_test_token", chat_id="555444")
        session = TelegramSession.objects.create(
            chat_id="555444",
            user=self.user1,
            is_authenticated=True,
            state="AUTHENTICATED_IDLE",
        )

        with patch.object(assistant, "send_text_response", return_value=True):
            # Query camera status -> State transitions to AWAITING_FEEDBACK
            assistant.handle_incoming_message("camera status", chat_id="555444")
            session.refresh_from_db()
            self.assertEqual(session.state, "AWAITING_FEEDBACK")

            # Reply YES -> Feedback saved in database
            res_fb = assistant.handle_incoming_message("YES", chat_id="555444")
            self.assertTrue(res_fb["success"])
            self.assertIn("FEEDBACK RECORDED", res_fb["message"])

            fb = TelegramFeedback.objects.filter(chat_id="555444").first()
            self.assertIsNotNone(fb)
            self.assertTrue(fb.is_helpful)
            self.assertEqual(fb.intent, "camera_status")

            session.refresh_from_db()
            self.assertEqual(session.state, "AUTHENTICATED_IDLE")

    def test_no_emojis_in_all_reports(self):
        from .openclaw import OpenClawAssistant
        import re

        assistant = OpenClawAssistant(bot_token="dummy_test_token", chat_id="333222")
        TelegramSession.objects.create(
            chat_id="333222",
            user=self.user1,
            is_authenticated=True,
            state="AUTHENTICATED_IDLE",
        )

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
            res = assistant.interpret_and_query(query, user=self.user1)
            msg = res["message"]
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

    def test_settings_page_telegram_card(self):
        self.client.login(username="alice", password="password123")
        res = self.client.get(reverse("nvr:settings"))
        self.assertEqual(res.status_code, 200)
        content = res.content.decode()
        self.assertIn("Telegram Intrusion Alert", content)
        self.assertIn("Test Telegram Alert", content)
        self.assertIn("btn-test-telegram-alert", content)

    def test_test_telegram_alert_api(self):
        self.client.login(username="alice", password="password123")
        from unittest.mock import patch

        mock_result = (True, {
            "status_code": 200,
            "ok": True,
            "response": {"ok": True, "result": {"message_id": 1337}},
            "chat_id": "1448272968",
        })

        with patch("nvr.views.send_telegram_alert", return_value=mock_result):
            res = self.client.post(reverse("nvr:test_telegram_alert"))
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["success"])
            self.assertEqual(data["status_code"], 200)
            self.assertEqual(data["chat_id"], "1448272968")


