"""
nvr/assistant/service.py
------------------------
Core internal SemanticEdge Assistant Service.
Coordinates:
- AlertConversation lifecycle
- ChatMessage persistence
- Active alert/event context preservation
- Controlled NVR tool routing
- LLM response generation
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from django.contrib.auth.models import User
from django.utils import timezone

from .llm import BaseLLMProvider, get_llm_provider
from .tools import NVRTools

logger = logging.getLogger("semanticedge.assistant.service")


class AssistantService:
    """
    Orchestration service for operator surveillance conversations and investigations.
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or get_llm_provider()

    def get_or_create_conversation(
        self,
        user: User,
        event_id: Optional[int] = None,
        camera_id: Optional[int] = None,
        title: Optional[str] = None,
    ):
        """
        Retrieves an existing conversation for an event or creates a new one,
        seeding it with the originating alert/event context.
        """
        from nvr.models import AlertConversation, Camera, ChatMessage, DetectionEvent

        event = None
        camera = None

        if event_id:
            event = DetectionEvent.objects.filter(id=event_id).select_related("camera").first()
            if event:
                camera = event.camera

        if not camera and camera_id:
            camera = Camera.objects.filter(id=camera_id).first()

        # Check for existing conversation for this user and event
        if event:
            conv = AlertConversation.objects.filter(user=user, event=event).first()
            if conv:
                return conv

        # Generate descriptive title
        if not title:
            if event:
                status_str = f" ({event.line_crossing_status})" if event.line_crossing_status and event.line_crossing_status != "none" else ""
                title = f"{event.class_name.title()} #{event.track_id} on {event.camera.name}{status_str}"
            elif camera:
                title = f"Camera Investigation: {camera.name}"
            else:
                title = f"Investigation Session - {timezone.now():%b %d, %H:%M}"

        context_snapshot = {}
        if event:
            context_snapshot = {
                "event_id": event.id,
                "track_id": event.track_id,
                "class_name": event.class_name,
                "confidence": round(event.confidence, 4),
                "camera_id": event.camera.id,
                "camera_name": event.camera.name,
                "status": event.line_crossing_status,
                "description": event.description or "",
                "snapshot_url": event.snapshot_path,
                "timestamp": event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        elif camera:
            context_snapshot = {
                "camera_id": camera.id,
                "camera_name": camera.name,
            }

        conv = AlertConversation.objects.create(
            user=user,
            event=event,
            camera=camera,
            title=title,
            context_snapshot=context_snapshot,
        )

        # Seed the conversation with an initial system greeting if bound to an event
        if event:
            intro = (
                f"Investigation opened for **{event.class_name.title()} #{event.track_id}** "
                f"detected on **{event.camera.name}** at {event.created_at:%Y-%m-%d %H:%M:%S}.\n"
                f"Status: `{event.line_crossing_status}` | Confidence: {int(event.confidence * 100)}%.\n"
                f"I have loaded the alert context. You can ask for snapshot evidence, movement history, "
                f"related detections, or camera status."
            )
            ChatMessage.objects.create(
                conversation=conv,
                sender="system",
                content=intro,
                evidence={
                    "event_id": event.id,
                    "snapshot_url": event.snapshot_path,
                    "camera_name": event.camera.name,
                    "class_name": event.class_name,
                    "track_id": event.track_id,
                },
            )

        return conv

    def get_conversation(self, conversation_id: int, user: User):
        """
        Retrieves conversation with user access control.
        """
        from nvr.models import AlertConversation

        qs = AlertConversation.objects.select_related("event", "camera")
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(user=user)
        return qs.filter(id=conversation_id).first()

    def list_conversations(self, user: User, limit: int = 30):
        """
        Lists recent conversations for the user.
        """
        from nvr.models import AlertConversation

        qs = AlertConversation.objects.select_related("event", "camera")
        if not (user.is_staff or user.is_superuser):
            qs = qs.filter(user=user)
        return list(qs.order_by("-updated_at")[:limit])

    def post_user_message(self, conversation_id: int, user: User, text: str) -> dict[str, Any]:
        """
        Submits operator message, evaluates context & tools, queries LLM provider,
        and persists the assistant's reply.
        """
        from nvr.models import ChatMessage

        conv = self.get_conversation(conversation_id, user)
        if not conv:
            return {"success": False, "error": "Conversation not found or access denied."}

        clean_text = text.strip()
        if not clean_text:
            return {"success": False, "error": "Message content cannot be empty."}

        # 1. Save User Message
        user_msg = ChatMessage.objects.create(
            conversation=conv,
            sender="user",
            content=clean_text,
        )

        # 2. Compile conversation history
        history_msgs = list(
            conv.messages.exclude(id=user_msg.id).order_by("created_at")[:12]
        )
        history = [
            {"sender": m.sender, "content": m.content, "evidence": m.evidence}
            for m in history_msgs
        ]

        # 3. Compile context
        context = conv.get_context_summary()

        # 4. Generate response via LLM Provider
        resp = self.provider.generate_response(
            prompt=clean_text,
            history=history,
            context=context,
            user=user,
        )

        reply_content = resp.get("content", "")
        reply_evidence = resp.get("evidence", {}) or {}
        if resp.get("suggested_actions"):
            reply_evidence["suggested_actions"] = resp["suggested_actions"]

        # 5. Save Assistant Message
        assistant_msg = ChatMessage.objects.create(
            conversation=conv,
            sender="assistant",
            content=reply_content,
            evidence=reply_evidence,
        )

        # 6. Update conversation timestamp
        conv.save(update_fields=["updated_at"])

        return {
            "success": True,
            "conversation_id": conv.id,
            "user_message": {
                "id": user_msg.id,
                "sender": user_msg.sender,
                "content": user_msg.content,
                "created_at": user_msg.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "assistant_message": {
                "id": assistant_msg.id,
                "sender": assistant_msg.sender,
                "content": assistant_msg.content,
                "evidence": assistant_msg.evidence,
                "created_at": assistant_msg.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            },
        }

    def get_status_diagnostics(self, user: User) -> dict[str, Any]:
        """
        Diagnostic summary of the assistant service.
        """
        from nvr.models import AlertConversation, ChatMessage

        conv_count = AlertConversation.objects.filter(user=user).count() if not user.is_staff else AlertConversation.objects.count()
        msg_count = ChatMessage.objects.count()

        return {
            "status": "ONLINE",
            "provider": self.provider.__class__.__name__,
            "real_time_loop_decoupled": True,
            "total_conversations": conv_count,
            "total_messages": msg_count,
            "tools_registered": [
                "get_alert_details",
                "get_latest_intrusion",
                "get_latest_image",
                "get_track_history",
                "get_related_detections",
                "get_events_around_timestamp",
                "get_camera_status",
                "get_system_telemetry",
                "get_detection_statistics",
                "get_monitoring_zones",
                "get_export_records",
            ],
        }
