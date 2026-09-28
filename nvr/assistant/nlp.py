"""
nvr/assistant/nlp.py
--------------------
Intent recognition and query parsing for the SemanticEdge Internal Assistant.
Preserves and modernizes the surveillance-specific NLP parsing patterns originally
developed in OpenClaw.
"""

from __future__ import annotations

import re
from typing import Any


class AssistantNLPEngine:
    """
    Parses natural language operator requests into structured surveillance intents and parameters.
    """

    INTENT_LATEST_INTRUSION = "latest_intrusion"
    INTENT_LATEST_IMAGE = "latest_image"
    INTENT_TRACK_ID = "track_id"
    INTENT_EVENT_ID = "event_id"
    INTENT_YESTERDAY_ALERTS = "yesterday_alerts"
    INTENT_ALERTS_FILTER = "alerts_filter"
    INTENT_CAMERA_STATUS = "camera_status"
    INTENT_SYSTEM_STATUS = "system_status"
    INTENT_STATS = "detection_statistics"
    INTENT_ZONES = "monitoring_zones"
    INTENT_EXPORTS = "export_requests"
    INTENT_RELATED = "related_detections"
    INTENT_HELP = "help"
    INTENT_GENERAL = "general"

    def parse_intent(self, text: str) -> tuple[str, dict[str, Any]]:
        raw = text.strip()
        cleaned = raw.lower()

        # 1. Help & Capabilities
        if cleaned in ["help", "/help", "commands", "menu", "what can you do", "capabilities"]:
            return self.INTENT_HELP, {"raw_query": raw}

        # 2. Evidence search by Event ID (e.g. "event 12", "event id 12", "snapshot for event 12")
        event_match = re.search(r"(?:event\s*id|event|detection\s*id)\s*[:#]?\s*(\d+)", cleaned)
        if event_match:
            eid = int(event_match.group(1))
            return self.INTENT_EVENT_ID, {"event_id": eid, "raw_query": raw}

        # 3. Evidence search by Track ID (e.g. "send image for Track ID 5", "track 5", "target #5")
        track_match = re.search(r"(?:track\s*id|track|target)\s*[:#]?\s*(\d+)", cleaned)
        if track_match:
            tid = int(track_match.group(1))
            return self.INTENT_TRACK_ID, {"track_id": tid, "raw_query": raw}

        # 4. Related detections
        if any(w in cleaned for w in ["related detections", "related events", "nearby events", "co-occurring", "around this time"]):
            return self.INTENT_RELATED, {"raw_query": raw}

        # 5. Camera Status / Fleet
        if any(w in cleaned for w in [
            "camera status", "active cameras", "list cameras", "show cameras",
            "cameras online", "camera fleet", "view cameras", "all cameras"
        ]) or cleaned in ["cameras", "camera"]:
            return self.INTENT_CAMERA_STATUS, {"raw_query": raw}

        # 6. System Status / Telemetry / Storage
        if any(w in cleaned for w in [
            "system status", "server health", "storage usage", "disk usage",
            "storage status", "disk status", "system health", "telemetry", "server status", "ram", "cpu"
        ]):
            return self.INTENT_SYSTEM_STATUS, {"raw_query": raw}

        # 7. Detection Statistics
        if any(w in cleaned for w in [
            "detection statistics", "detection stats", "statistics", "stats",
            "today stats", "today's stats", "detection summary", "activity summary", "analytics"
        ]):
            return self.INTENT_STATS, {"raw_query": raw}

        # 8. Monitoring Zones / Tripwires
        if any(w in cleaned for w in [
            "monitoring zones", "zones", "show zones", "list zones",
            "tripwires", "restricted zones", "active zones"
        ]):
            return self.INTENT_ZONES, {"raw_query": raw}

        # 9. Video / Log Exports
        if any(w in cleaned for w in [
            "export requests", "export video", "recent exports",
            "export history", "export logs", "export report", "exports"
        ]):
            return self.INTENT_EXPORTS, {"raw_query": raw}

        # 10. Filtered Alerts: Date or Camera
        if "yesterday" in cleaned:
            return self.INTENT_YESTERDAY_ALERTS, {"raw_query": raw}

        if any(w in cleaned for w in ["alerts today", "today's alerts", "today alerts", "today intrusion", "today breaches"]):
            return self.INTENT_ALERTS_FILTER, {"filter_type": "date", "date": "today", "raw_query": raw}

        date_match = re.search(r"(?:alerts\s+(?:on|for)\s+)?(\d{4}-\d{2}-\d{2})", cleaned)
        if date_match:
            return self.INTENT_ALERTS_FILTER, {"filter_type": "date", "date": date_match.group(1), "raw_query": raw}

        cam_alert_match = re.search(r"alerts\s+(?:for|on|from)\s+(?:camera\s+)?([a-zA-Z0-9_\- ]+)", cleaned)
        if cam_alert_match:
            cam_query = cam_alert_match.group(1).strip()
            return self.INTENT_ALERTS_FILTER, {"filter_type": "camera", "camera": cam_query, "raw_query": raw}

        # 11. Latest intrusion inquiry
        if any(w in cleaned for w in [
            "latest intrusion", "recent intrusion", "last intrusion",
            "show intrusion", "recent breach", "last breach", "intrusion alert", "intrusion", "breach"
        ]):
            return self.INTENT_LATEST_INTRUSION, {"raw_query": raw}

        # 12. Latest image / detection snapshot
        if (
            any(w in cleaned for w in ["latest", "recent", "newest", "last"])
            and any(w in cleaned for w in ["image", "photo", "snapshot", "picture", "frame", "event", "detection"])
        ) or cleaned in ["show latest image", "latest image", "send image", "show image", "photo", "snapshot", "image"]:
            return self.INTENT_LATEST_IMAGE, {"raw_query": raw}

        # 13. Fallback General
        return self.INTENT_GENERAL, {"raw_query": raw}
