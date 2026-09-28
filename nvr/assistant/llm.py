"""
nvr/assistant/llm.py
-------------------
LLM Provider abstraction for the SemanticEdge Internal Assistant.
Keeps LLM dependencies decoupled and swappable (Gemini, Local/Open-weights, or deterministic Rule-based).
Ensures the LLM NEVER executes raw database queries.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Optional

from django.conf import settings
from .nlp import AssistantNLPEngine
from .tools import NVRTools

logger = logging.getLogger("semanticedge.assistant.llm")


class BaseLLMProvider(ABC):
    """Abstract interface for Assistant LLM backends."""

    @abstractmethod
    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, Any]],
        context: dict[str, Any],
        user: Any = None,
    ) -> dict[str, Any]:
        """
        Generate assistant response.
        Returns:
            {
                "content": str,
                "evidence": dict,
                "suggested_actions": list[dict],
            }
        """
        pass


class RuleBasedNVRProvider(BaseLLMProvider):
    """
    Deterministic, high-performance rule-based NVR surveillance assistant.
    Interprets natural language queries using AssistantNLPEngine, calls controlled NVRTools,
    and formats verified surveillance reports with real evidence. Zero hallucination.
    """

    def __init__(self):
        self.nlp = AssistantNLPEngine()

    def generate_response(
        self,
        prompt: str,
        history: list[dict[str, Any]],
        context: dict[str, Any],
        user: Any = None,
    ) -> dict[str, Any]:
        intent, params = self.nlp.parse_intent(prompt)
        evidence: dict[str, Any] = {}
        suggested_actions: list[dict[str, Any]] = []

        # Check if conversation is bound to a specific event
        active_event_id = context.get("event_id")
        active_track_id = context.get("track_id")
        active_camera_id = context.get("camera_id")

        # ── 1. Event ID or specific active event ──────────────────────
        if intent == AssistantNLPEngine.INTENT_EVENT_ID:
            eid = params.get("event_id")
            data = NVRTools.get_alert_details(eid, user=user)
            if data.get("found"):
                content = (
                    "SEMANTICEDGE EVIDENCE RECORD\n"
                    "----------------------------------------\n"
                    f"EVENT ID    : #{data['id']}\n"
                    f"CAMERA      : {data['camera_name']}\n"
                    f"OBJECT      : {data['class_name'].title()} (Track #{data['track_id']})\n"
                    f"CONFIDENCE  : {data['confidence_pct']}\n"
                    f"TIMESTAMP   : {data['timestamp']}\n"
                    f"STATUS      : {data['line_crossing_status']}\n"
                    f"DESCRIPTION : {data['description'] or 'Detection snapshot record.'}\n"
                    "----------------------------------------"
                )
                evidence = {
                    "event_id": data["id"],
                    "snapshot_url": data["snapshot_url"],
                    "snapshot_exists": data["snapshot_exists"],
                    "camera_name": data["camera_name"],
                    "class_name": data["class_name"],
                    "track_id": data["track_id"],
                }
                suggested_actions.append({
                    "label": "Inspect in Review",
                    "action": "navigate_review",
                    "params": {"camera": data["camera_id"], "class": data["class_name"], "track_id": data["track_id"]},
                })
            else:
                content = f"Event #{eid} could not be found or you do not have permission to view it."

            return {"content": content, "evidence": evidence, "suggested_actions": suggested_actions}

        # ── 2. Track ID or Active Track ───────────────────────────────
        if intent == AssistantNLPEngine.INTENT_TRACK_ID or ("track" in prompt.lower() and active_track_id):
            tid = params.get("track_id") or active_track_id
            data = NVRTools.get_track_history(tid, camera_id=active_camera_id, user=user)
            if data.get("found"):
                lines = [
                    "SEMANTICEDGE TRACK HISTORY RECORD",
                    "----------------------------------------",
                    f"TRACK ID    : #{data['track_id']} ({data['class_name'].title()})",
                    f"TOTAL LOGS  : {data['total_records']} detection points",
                    f"LATEST SEEN : {data['latest_timestamp']} on {data['latest_camera']}",
                    "----------------------------------------",
                    "RECENT TRACK OBSERVATIONS:",
                ]
                for obs in data["history"][:5]:
                    lines.append(f"- {obs['timestamp']} | {obs['camera_name']} | {obs['status']}")
                lines.append("----------------------------------------")
                content = "\n".join(lines)
                evidence = {
                    "track_id": data["track_id"],
                    "event_id": data["latest_event_id"],
                    "snapshot_url": data["snapshot_url"],
                    "snapshot_exists": data["snapshot_exists"],
                }
                suggested_actions.append({
                    "label": "Review Full Track History",
                    "action": "navigate_review",
                    "params": {"track_id": data["track_id"], "class": data["class_name"]},
                })
            else:
                content = f"No detection records found for Track #{tid}."

            return {"content": content, "evidence": evidence, "suggested_actions": suggested_actions}

        # ── 3. Latest Intrusion ───────────────────────────────────────
        if intent == AssistantNLPEngine.INTENT_LATEST_INTRUSION:
            data = NVRTools.get_latest_intrusion(user=user)
            if data.get("found"):
                content = (
                    "SEMANTICEDGE SURVEILLANCE REPORT\n"
                    "LATEST INTRUSION INCIDENT\n"
                    "----------------------------------------\n"
                    f"EVENT ID    : #{data['id']}\n"
                    f"CAMERA      : {data['camera_name']}\n"
                    f"OBJECT      : {data['class_name'].title()} (Track #{data['track_id']})\n"
                    f"STATUS      : {data['line_crossing_status']}\n"
                    f"CONFIDENCE  : {data['confidence_pct']}\n"
                    f"TIMESTAMP   : {data['timestamp']}\n"
                    f"DESCRIPTION : {data['description'] or 'Perimeter breach detected.'}\n"
                    "----------------------------------------"
                )
                evidence = {
                    "event_id": data["id"],
                    "snapshot_url": data["snapshot_url"],
                    "snapshot_exists": data["snapshot_exists"],
                    "camera_name": data["camera_name"],
                    "class_name": data["class_name"],
                    "track_id": data["track_id"],
                }
                suggested_actions.append({
                    "label": "View in Review",
                    "action": "navigate_review",
                    "params": {"camera": data["camera_id"], "class": data["class_name"], "event_id": data["id"]},
                })
            else:
                content = "No intrusion incidents found in the NVR records."

            return {"content": content, "evidence": evidence, "suggested_actions": suggested_actions}

        # ── 4. Latest Image / Snapshot ────────────────────────────────
        if intent == AssistantNLPEngine.INTENT_LATEST_IMAGE:
            # If the user asks for "image", "photo", or "snapshot" in an active event conversation, serve that event's snapshot!
            if active_event_id and any(w in prompt.lower() for w in ["this", "here", "current", "snapshot", "photo", "image"]):
                data = NVRTools.get_alert_details(active_event_id, user=user)
            else:
                data = NVRTools.get_latest_image(user=user)

            if data.get("found"):
                content = (
                    "SEMANTICEDGE EVIDENCE CAPTURE\n"
                    "----------------------------------------\n"
                    f"EVENT ID    : #{data['id']}\n"
                    f"CAMERA      : {data['camera_name']}\n"
                    f"OBJECT      : {data['class_name'].title()} (Track #{data['track_id']})\n"
                    f"CONFIDENCE  : {data['confidence_pct']}\n"
                    f"TIMESTAMP   : {data['timestamp']}\n"
                    f"FRAME       : #{data['frame_number']}\n"
                    "----------------------------------------"
                )
                evidence = {
                    "event_id": data["id"],
                    "snapshot_url": data["snapshot_url"],
                    "snapshot_exists": data["snapshot_exists"],
                    "camera_name": data["camera_name"],
                    "class_name": data["class_name"],
                    "track_id": data["track_id"],
                }
            else:
                content = "No image snapshots are currently available in the database."

            return {"content": content, "evidence": evidence, "suggested_actions": suggested_actions}

        # ── 5. Related Detections / Co-occurring Events ───────────────
        if intent == AssistantNLPEngine.INTENT_RELATED or (active_event_id and "related" in prompt.lower()):
            target_eid = active_event_id or context.get("event_id")
            if target_eid:
                data = NVRTools.get_related_detections(target_eid, window_seconds=180, user=user)
                if data.get("found") and data["related_count"] > 0:
                    lines = [
                        "SEMANTICEDGE TEMPORAL CORRELATION",
                        f"CORRELATED WITH EVENT #{target_eid} (Window: ±180s)",
                        "----------------------------------------",
                    ]
                    for idx, rel in enumerate(data["related_detections"][:5], start=1):
                        diff_str = f"+{rel['time_diff_seconds']}s" if rel['time_diff_seconds'] >= 0 else f"{rel['time_diff_seconds']}s"
                        lines.append(f"[{idx}] Event #{rel['id']} | {rel['camera_name']} | {rel['class_name'].title()} #{rel['track_id']} ({diff_str})")
                    lines.append("----------------------------------------")
                    content = "\n".join(lines)
                    suggested_actions.append({
                        "label": "Review Correlated Window",
                        "action": "navigate_review",
                        "params": {"time": "1h"},
                    })
                else:
                    content = f"No other detections were observed within ±180 seconds of Event #{target_eid}."
            else:
                content = "Please select a specific event or alert in Explore to inspect related detections."

            return {"content": content, "evidence": evidence, "suggested_actions": suggested_actions}

        # ── 6. Camera Status / Fleet ──────────────────────────────────
        if intent == AssistantNLPEngine.INTENT_CAMERA_STATUS:
            data = NVRTools.get_camera_status(user=user)
            lines = [
                "SEMANTICEDGE CAMERA FLEET STATUS",
                "----------------------------------------",
                f"TOTAL FEEDS  : {data['total_cameras']}",
                f"ONLINE FEEDS : {data['active_cameras']}",
                "----------------------------------------",
            ]
            for idx, c in enumerate(data["cameras"], start=1):
                lines.append(
                    f"[{idx}] {c['name']} ({c['status']})\n"
                    f"    Source  : {c['source_url']}\n"
                    f"    Mode    : {c['scene_mode']}\n"
                    f"    Last Evt: {c['last_event_time'] or 'None'}"
                )
            lines.append("----------------------------------------")
            content = "\n".join(lines)
            return {"content": content, "evidence": {}, "suggested_actions": []}

        # ── 7. System Status / Telemetry ──────────────────────────────
        if intent == AssistantNLPEngine.INTENT_SYSTEM_STATUS:
            data = NVRTools.get_system_telemetry(user=user)
            content = (
                "SEMANTICEDGE SYSTEM TELEMETRY\n"
                "----------------------------------------\n"
                f"SERVER STATUS : {data['server_status']}\n"
                f"PLATFORM      : {data['platform']}\n"
                f"CPU USAGE     : {data['cpu_percent']}%\n"
                f"RAM USAGE     : {data['ram_used_gb']} GB used of {data['ram_total_gb']} GB\n"
                f"DISK STORAGE  : {data['disk_used_gb']} GB / {data['disk_total_gb']} GB ({data['disk_percent']}% used)\n"
                f"MEDIA ARCHIVE : {data['media_archive_mb']} MB\n"
                f"DETECTION LOGS: {data['detection_events_logged']} events\n"
                f"CAMERA FEEDS  : {data['cameras_active']} active\n"
                f"MONITOR ZONES : {data['active_monitoring_zones']} active\n"
                "----------------------------------------"
            )
            return {"content": content, "evidence": {}, "suggested_actions": []}

        # ── 8. Detection Statistics ───────────────────────────────────
        if intent in [AssistantNLPEngine.INTENT_STATS, AssistantNLPEngine.INTENT_YESTERDAY_ALERTS]:
            date_arg = "yesterday" if intent == AssistantNLPEngine.INTENT_YESTERDAY_ALERTS else "today"
            data = NVRTools.get_detection_statistics(date_str=date_arg, user=user)
            lines = [
                "SEMANTICEDGE DETECTION STATISTICS",
                "----------------------------------------",
                f"PERIOD        : {data['period']}",
                f"TOTAL EVENTS  : {data['total_events']}",
                f"INTRUSIONS    : {data['intrusions']}",
                f"ATTENDANCE    : {data['attendance']}",
                "----------------------------------------",
                "CLASSIFICATION BREAKDOWN:",
            ]
            if data["class_breakdown"]:
                for cls, count in data["class_breakdown"].items():
                    lines.append(f"- {cls.title():<12}: {count} detections")
            else:
                lines.append("- No detections recorded in this period.")
            lines.append("----------------------------------------")
            content = "\n".join(lines)
            return {"content": content, "evidence": {}, "suggested_actions": []}

        # ── 9. Monitoring Zones ───────────────────────────────────────
        if intent == AssistantNLPEngine.INTENT_ZONES:
            data = NVRTools.get_monitoring_zones(user=user)
            lines = [
                "SEMANTICEDGE MONITORING ZONES",
                "----------------------------------------",
                f"CONFIGURED ZONES: {data['total_zones']}",
                "----------------------------------------",
            ]
            if data["zones"]:
                for idx, z in enumerate(data["zones"], start=1):
                    target_str = ", ".join(z["target_classes"])
                    status_str = "ACTIVE" if z["is_active"] else "INACTIVE"
                    lines.append(
                        f"[{idx}] {z['name']} ({status_str})\n"
                        f"    Camera : {z['camera_name']}\n"
                        f"    Type   : {z['zone_type']}\n"
                        f"    Targets: {target_str}"
                    )
            else:
                lines.append("No monitoring zones or tripwires configured.")
            lines.append("----------------------------------------")
            content = "\n".join(lines)
            return {"content": content, "evidence": {}, "suggested_actions": []}

        # ── 10. Video / Log Exports ───────────────────────────────────
        if intent == AssistantNLPEngine.INTENT_EXPORTS:
            data = NVRTools.get_export_records(user=user)
            lines = [
                "SEMANTICEDGE EXPORT ARCHIVE",
                "----------------------------------------",
                f"AVAILABLE EXPORTS: {data['total_files']} files",
                "----------------------------------------",
            ]
            if data["recent_exports"]:
                for exp in data["recent_exports"][:5]:
                    lines.append(f"- {exp['filename']} ({exp['size_mb']} MB)\n  URL: {exp['url']}")
            else:
                lines.append("No video clips currently archived in media/exports/.")
            lines.append("----------------------------------------")
            content = "\n".join(lines)
            return {"content": content, "evidence": {}, "suggested_actions": []}

        # ── 11. Help / Capabilities ───────────────────────────────────
        if intent == AssistantNLPEngine.INTENT_HELP:
            content = (
                "SEMANTICEDGE SECURITY ASSISTANT\n"
                "OPERATIONAL CAPABILITIES\n"
                "----------------------------------------\n"
                "- 'latest intrusion'    : View most recent perimeter breach & snapshot\n"
                "- 'show latest image'   : View latest captured snapshot\n"
                "- 'evidence track 5'    : Retrieve snapshot & movement history for Track #5\n"
                "- 'event 12'            : Retrieve snapshot & details for Event #12\n"
                "- 'related detections'  : Find co-occurring detections around this event\n"
                "- 'alerts today'        : Summary of today's events\n"
                "- 'yesterday alerts'    : Security events logged yesterday\n"
                "- 'camera status'       : Real-time fleet health & active feeds\n"
                "- 'system status'       : CPU, RAM, disk, and media storage\n"
                "- 'detection statistics': Breakdown by object class\n"
                "- 'monitoring zones'    : Active tripwires and restricted zones\n"
                "- 'export requests'     : Recent video exports\n"
                "----------------------------------------"
            )
            return {"content": content, "evidence": {}, "suggested_actions": []}

        # ── 12. General / Conversational Response ─────────────────────
        # If in active event context, provide context-aware response
        if active_event_id:
            event_data = NVRTools.get_alert_details(active_event_id, user=user)
            if event_data.get("found"):
                content = (
                    f"Active Investigation: {event_data['class_name'].title()} #{event_data['track_id']} "
                    f"on {event_data['camera_name']} ({event_data['timestamp']}).\n\n"
                    f"Status: {event_data['line_crossing_status']}.\n"
                    f"You can ask me to retrieve the snapshot image, check movement history, "
                    f"find related detections, or inspect fleet status."
                )
                evidence = {
                    "event_id": event_data["id"],
                    "snapshot_url": event_data["snapshot_url"],
                    "snapshot_exists": event_data["snapshot_exists"],
                }
                return {"content": content, "evidence": evidence, "suggested_actions": []}

        content = (
            "SEMANTICEDGE SECURITY ASSISTANT\n"
            "----------------------------------------\n"
            "Request received. You can ask operational questions regarding:\n"
            "- Intrusion alerts: 'latest intrusion'\n"
            "- Target history: 'track #5'\n"
            "- Snapshots: 'show latest image' or 'event 12'\n"
            "- Cameras & fleet: 'camera status'\n"
            "- System telemetry: 'system status'\n"
            "- Activity breakdown: 'detection statistics'\n"
            "----------------------------------------\n"
            "Type 'help' for full command capabilities."
        )
        return {"content": content, "evidence": {}, "suggested_actions": []}


def get_llm_provider() -> BaseLLMProvider:
    """Factory function returning the active assistant provider."""
    # We use RuleBasedNVRProvider by default as it is zero-dependency, ultra-fast,
    # strictly bounded, and directly satisfies all NVR controlled tool operations.
    return RuleBasedNVRProvider()
