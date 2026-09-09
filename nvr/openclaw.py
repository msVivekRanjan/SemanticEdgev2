"""
nvr/openclaw.py
--------------
Telegram Bot integration & OpenClaw Natural Language Backend Engine for SemanticEdge NVR.

Key Responsibilities:
1. send_telegram_alert:
   Dispatches instant intrusion alerts to Telegram configured via environment variables
   (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID). Professional CCTV surveillance report format (no emojis).

2. OpenClawNLPEngine:
   Acts strictly as a backend NLP engine. Interprets surveillance-specific requests:
   - "latest intrusion"
   - "show latest image"
   - "send image for Track ID 5"
   - "event 12"
   - "alerts today" / "show yesterday's alerts" / "alerts for Front Door"
   - "camera status" / "active cameras"
   - "system status" / "storage usage"
   - "detection statistics" / "today stats"
   - "monitoring zones"
   - "export requests"
   - Feedback ("yes" / "no")
   - Unsupported queries receive helpful operational guidance.

3. OpenClawAssistant:
   Coordinates end-to-end execution:
   - Telegram User Authentication against Django User database (/start, /login, /logout)
   - Interactive feedback collection (stored in TelegramFeedback database table)
   - SQLite queries against Camera, DetectionEvent, MonitoringZone
   - Snapshot disk resolution
   - Structured CCTV reports without emojis
"""

from __future__ import annotations

import logging
import os
import platform
import re
import shutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import psutil
import requests
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q
from django.utils import timezone

logger = logging.getLogger("semanticedge.openclaw")

TELEGRAM_API_BASE = "https://api.telegram.org"

# Recognized Intent Constants
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
INTENT_FEEDBACK = "feedback"
INTENT_HELP = "help"
INTENT_LOGIN = "login"
INTENT_LOGOUT = "logout"
INTENT_GENERAL_CONVERSATION = "general_conversation"


def get_telegram_config() -> tuple[str, str]:
    """
    Retrieve Telegram bot token and target chat ID.
    Directly checks .env and settings, and prevents the bot ID from being used as target chat ID.
    """
    token = getattr(settings, "TELEGRAM_BOT_TOKEN", "") or os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(settings, "TELEGRAM_CHAT_ID", "") or os.getenv("TELEGRAM_CHAT_ID", "")

    # Direct fallback read from .env if empty or misconfigured
    env_file = Path(getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent)) / ".env"
    if env_file.is_file():
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("TELEGRAM_BOT_TOKEN=") and not token:
                        token = line.split("=", 1)[1].strip().strip('"').strip("'")
                    elif line.startswith("TELEGRAM_CHAT_ID="):
                        env_chat_id = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if env_chat_id:
                            chat_id = env_chat_id
        except Exception:
            pass

    token = token.strip()
    chat_id = chat_id.strip()

    # Safety Guard: Telegram bots cannot message themselves.
    bot_id = token.split(":", 1)[0] if ":" in token else ""
    if bot_id and chat_id == bot_id:
        logger.warning(
            f"[OpenClaw] TELEGRAM_CHAT_ID '{chat_id}' matches BOT_ID. "
            f"Telegram rejects bot-to-bot messaging. Falling back to default user ID '1448272968'."
        )
        chat_id = "1448272968"

    return token, chat_id


def send_telegram_alert(event: Any, custom_caption: str | None = None, sync: bool = False) -> tuple[bool, dict[str, Any]] | bool:
    """
    Dispatch an intrusion alert to Telegram in professional CCTV format (no emojis).
    Supports asynchronous and synchronous dispatch.
    """
    token, chat_id = get_telegram_config()
    event_id = getattr(event, "id", None) or getattr(event, "pk", "test")
    camera_name = getattr(getattr(event, "camera", None), "name", "Active Camera")
    cls_name = getattr(event, "class_name", "Object").capitalize()
    track_id = getattr(event, "track_id", -1)
    status = getattr(event, "line_crossing_status", "Restricted Area Intrusion")
    created = getattr(event, "created_at", None)
    if created:
        time_str = created.strftime("%Y-%m-%d %H:%M:%S")
    else:
        time_str = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

    # Stage 3: [send_telegram_alert() called]
    stage3_msg = f"[send_telegram_alert() called] Event ID={event_id} | Track=#{track_id} | Camera='{camera_name}' | Target Chat ID='{chat_id}'"
    logger.info(stage3_msg)
    print(stage3_msg)

    if not token or not chat_id:
        err_msg = "[ALERT FAILED] Telegram BOT_TOKEN or CHAT_ID not configured."
        logger.warning(err_msg)
        print(err_msg)
        if sync:
            return False, {"error": err_msg, "status_code": 0}
        return False

    zone_name = status.split(":", 1)[1].strip() if ":" in status else (status or "Restricted Area")
    conf_pct = getattr(event, "confidence", 0.0)
    conf_str = f"{int(conf_pct * 100)}%" if conf_pct else "N/A"

    message = (
        "SEMANTICEDGE INTRUSION ALERT\n"
        "----------------------------------------\n"
        f"CAMERA      : {camera_name}\n"
        f"ZONE        : {zone_name}\n"
        f"OBJECT      : {cls_name}\n"
        f"TRACK ID    : #{track_id}\n"
        f"CONFIDENCE  : {conf_str}\n"
        f"TIMESTAMP   : {time_str}\n"
        f"STATUS      : Restricted Area Breach\n"
        "----------------------------------------\n"
        "Restricted area breach detected."
    )

    url = f"{TELEGRAM_API_BASE}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": True,
    }

    # Stage 4: [Telegram payload created]
    masked_token = f"{token[:8]}...{token[-4:]}" if len(token) > 12 else "***"
    stage4_msg = (
        f"[Telegram payload created] Endpoint: POST https://api.telegram.org/bot{masked_token}/sendMessage | "
        f"Target Chat: {chat_id} | Message Length: {len(message)} chars"
    )
    logger.info(stage4_msg)
    print(stage4_msg)

    def _execute_post() -> tuple[bool, dict[str, Any]]:
        stage5_msg = "[Telegram API request sent] Dispatching POST request to Telegram API (timeout=10s)..."
        logger.info(stage5_msg)
        print(stage5_msg)

        try:
            resp = requests.post(url, json=payload, timeout=10)
            raw_text = resp.text

            stage6_msg = f"[Telegram API response received] HTTP Status={resp.status_code} | Response: {raw_text}"
            logger.info(stage6_msg)
            print(stage6_msg)

            if resp.ok:
                resp_json = resp.json()
                msg_id = resp_json.get("result", {}).get("message_id", "unknown")
                stage7_msg = (
                    f"[Alert delivered successfully] Telegram Message ID={msg_id} delivered to chat {chat_id} "
                    f"for event {event_id} (#{track_id})"
                )
                logger.info(stage7_msg)
                print(stage7_msg)
                return True, {"status_code": resp.status_code, "ok": True, "response": resp_json, "chat_id": chat_id}
            else:
                err_stage_msg = f"[ALERT DELIVERY FAILED] HTTP {resp.status_code} from Telegram API: {raw_text}"
                logger.error(err_stage_msg)
                print(err_stage_msg)
                try:
                    err_json = resp.json()
                except Exception:
                    err_json = {"raw": raw_text}
                return False, {"status_code": resp.status_code, "ok": False, "error": err_json, "chat_id": chat_id}

        except Exception as exc:
            exc_msg = f"[ALERT DELIVERY EXCEPTION] Network or runtime exception during alert dispatch: {exc}"
            logger.error(exc_msg)
            print(exc_msg)
            return False, {"status_code": 500, "ok": False, "error": str(exc), "chat_id": chat_id}

    if sync:
        return _execute_post()

    thread = threading.Thread(target=_execute_post, daemon=False)
    thread.start()
    return True


class OpenClawNLPEngine:
    """
    Backend NLP Intent Engine for SemanticEdge NVR.
    Parses incoming messages into structured surveillance intents.
    """

    def parse_intent(self, text: str) -> tuple[str, dict[str, Any]]:
        raw = text.strip()
        cleaned = raw.lower()

        # 1. Auth & Session commands
        if cleaned in ["/logout", "logout", "sign out"]:
            return INTENT_LOGOUT, {"raw_query": raw}

        if cleaned in ["/help", "help", "/start", "start", "commands", "menu"]:
            return INTENT_HELP, {"raw_query": raw}

        if cleaned.startswith("/login"):
            parts = raw.split(maxsplit=2)
            username = parts[1] if len(parts) > 1 else ""
            password = parts[2] if len(parts) > 2 else ""
            return INTENT_LOGIN, {"username": username, "password": password, "raw_query": raw}

        # 2. Feedback queries
        if cleaned in ["yes", "y", "helpful", "good", "correct"]:
            return INTENT_FEEDBACK, {"helpful": True, "raw_feedback": cleaned, "raw_query": raw}
        if cleaned in ["no", "n", "unhelpful", "bad", "incorrect"]:
            return INTENT_FEEDBACK, {"helpful": False, "raw_feedback": cleaned, "raw_query": raw}

        # 3. Evidence search by Event ID (e.g. "event 12", "event id 12", "snapshot for event 12")
        event_match = re.search(r"(?:event\s*id|event|detection\s*id)\s*[:#]?\s*(\d+)", cleaned)
        if event_match:
            eid = int(event_match.group(1))
            return INTENT_EVENT_ID, {"event_id": eid, "raw_query": raw}

        # 4. Evidence search by Track ID (e.g. "send image for Track ID 5", "track 5", "target #5")
        track_match = re.search(r"(?:track\s*id|track|target)\s*[:#]?\s*(\d+)", cleaned)
        if track_match:
            tid = int(track_match.group(1))
            return INTENT_TRACK_ID, {"track_id": tid, "raw_query": raw}

        # 5. Camera Status / Fleet
        if any(w in cleaned for w in ["camera status", "active cameras", "list cameras", "show cameras", "cameras online", "camera fleet", "view cameras"]) or cleaned == "cameras":
            return INTENT_CAMERA_STATUS, {"raw_query": raw}

        # 6. System Status / Telemetry / Storage
        if any(w in cleaned for w in ["system status", "server health", "storage usage", "disk usage", "storage status", "disk status", "system health", "telemetry", "server status"]):
            return INTENT_SYSTEM_STATUS, {"raw_query": raw}

        # 7. Detection Statistics
        if any(w in cleaned for w in ["detection statistics", "detection stats", "statistics", "stats", "today stats", "today's stats", "detection summary", "activity summary", "analytics"]):
            return INTENT_STATS, {"raw_query": raw}

        # 8. Monitoring Zones / Tripwires
        if any(w in cleaned for w in ["monitoring zones", "zones", "show zones", "list zones", "tripwires", "restricted zones", "active zones"]):
            return INTENT_ZONES, {"raw_query": raw}

        # 9. Video / Log Exports
        if any(w in cleaned for w in ["export requests", "export video", "recent exports", "export history", "export logs", "export report", "exports"]):
            return INTENT_EXPORTS, {"raw_query": raw}

        # 10. Filtered Alerts: Date or Camera
        if "yesterday" in cleaned:
            is_intrusion = any(w in cleaned for w in ["intrusion", "breach", "alarm"])
            return INTENT_YESTERDAY_ALERTS, {"intrusion_only": is_intrusion, "raw_query": raw}

        if any(w in cleaned for w in ["alerts today", "today's alerts", "today alerts", "today intrusion", "today breaches"]):
            return INTENT_ALERTS_FILTER, {"filter_type": "date", "date": "today", "raw_query": raw}

        date_match = re.search(r"(?:alerts\s+(?:on|for)\s+)?(\d{4}-\d{2}-\d{2})", cleaned)
        if date_match:
            return INTENT_ALERTS_FILTER, {"filter_type": "date", "date": date_match.group(1), "raw_query": raw}

        cam_alert_match = re.search(r"alerts\s+(?:for|on|from)\s+(?:camera\s+)?([a-zA-Z0-9_\- ]+)", cleaned)
        if cam_alert_match:
            cam_query = cam_alert_match.group(1).strip()
            return INTENT_ALERTS_FILTER, {"filter_type": "camera", "camera": cam_query, "raw_query": raw}

        # 11. Latest intrusion inquiry
        if any(w in cleaned for w in ["latest intrusion", "recent intrusion", "last intrusion", "show intrusion", "recent breach", "last breach", "intrusion alert", "intrusion"]):
            return INTENT_LATEST_INTRUSION, {"raw_query": raw}

        # 12. Latest image / detection snapshot
        if (
            any(w in cleaned for w in ["latest", "recent", "newest", "last"])
            and any(w in cleaned for w in ["image", "photo", "snapshot", "picture", "frame", "event", "detection"])
        ) or cleaned in ["show latest image", "latest image", "send image", "show image"]:
            return INTENT_LATEST_IMAGE, {"raw_query": raw}

        if any(cleaned.startswith(p) for p in ["show latest", "send latest", "recent detection"]):
            return INTENT_LATEST_IMAGE, {"raw_query": raw}

        # 13. General conversation / Unsupported query
        return INTENT_GENERAL_CONVERSATION, {"raw_query": raw}


class OpenClawAssistant:
    """
    SemanticEdge NVR Security Assistant.
    Enforces user authentication against Django User database, processes natural-language
    surveillance queries, coordinates disk snapshot evidence, formats clean CCTV reports (no emojis),
    and records user feedback in the database.
    """

    def __init__(self, bot_token: str | None = None, chat_id: str | None = None) -> None:
        cfg_token, cfg_chat_id = get_telegram_config()
        self.bot_token = bot_token or cfg_token
        self.chat_id = chat_id or cfg_chat_id
        self.base_url = f"{TELEGRAM_API_BASE}/bot{self.bot_token}" if self.bot_token else ""
        self.nlp_engine = OpenClawNLPEngine()

    def get_or_create_session(self, chat_id: str):
        from nvr.models import TelegramSession
        session, _ = TelegramSession.objects.get_or_create(chat_id=str(chat_id))
        return session

    def resolve_snapshot_file(self, snapshot_rel_path: str) -> Optional[Path]:
        if not snapshot_rel_path:
            return None

        clean_rel = snapshot_rel_path.lstrip("/")
        if clean_rel.startswith("media/"):
            clean_rel = clean_rel[len("media/"):]

        media_root = Path(getattr(settings, "MEDIA_ROOT", Path(__file__).resolve().parent.parent / "media"))
        candidate = media_root / clean_rel
        if candidate.is_file():
            return candidate

        base_dir = Path(getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent))
        candidate2 = base_dir / snapshot_rel_path.lstrip("/")
        if candidate2.is_file():
            return candidate2

        direct = Path(snapshot_rel_path)
        if direct.is_file():
            return direct

        return None

    def query_sqlite_for_intent(self, intent: str, params: dict[str, Any], user: User | None = None) -> dict[str, Any]:
        """
        Execute read-only Django ORM queries against SQLite tables.
        Returns standardized CCTV surveillance report strings (no emojis).
        """
        from nvr.models import Camera, DetectionEvent, MonitoringZone, AttendanceRecord

        result: dict[str, Any] = {
            "event": None,
            "image_path": None,
            "message": "",
            "success": False,
        }

        # Base event queryset scoped to user if specified and not superuser
        event_qs = DetectionEvent.objects.all()
        cam_qs = Camera.objects.all()
        zone_qs = MonitoringZone.objects.all()

        if user and not (user.is_staff or user.is_superuser):
            event_qs = event_qs.filter(Q(user=user) | Q(camera__owner=user))
            cam_qs = cam_qs.filter(owner=user)
            zone_qs = zone_qs.filter(camera__owner=user)

        # ── 1. Track ID Query ──────────────────────────────────────────────
        if intent == INTENT_TRACK_ID:
            tid = params.get("track_id", -1)
            event = event_qs.filter(track_id=tid).order_by("-created_at").first()
            if event:
                img_file = self.resolve_snapshot_file(event.snapshot_path)
                status = event.line_crossing_status or "Normal Detection"
                msg = (
                    "SEMANTICEDGE EVIDENCE RECORD\n"
                    "----------------------------------------\n"
                    f"EVENT ID    : {event.id}\n"
                    f"CAMERA      : {event.camera.name}\n"
                    f"OBJECT      : {event.class_name.title()}\n"
                    f"TRACK ID    : #{event.track_id}\n"
                    f"CONFIDENCE  : {int(event.confidence * 100)}%\n"
                    f"TIMESTAMP   : {event.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"STATUS      : {status}\n"
                    f"DESCRIPTION : {event.description or 'Tracked target evidence snapshot.'}\n"
                    "----------------------------------------"
                )
                result.update({"event": event, "image_path": img_file, "message": msg, "success": True})
            else:
                result["message"] = (
                    "SEMANTICEDGE QUERY RESULT\n"
                    "----------------------------------------\n"
                    f"No detection records found for Track ID #{tid}."
                )
            return result

        # ── 2. Event ID Query ──────────────────────────────────────────────
        if intent == INTENT_EVENT_ID:
            eid = params.get("event_id", -1)
            event = event_qs.filter(id=eid).first()
            if event:
                img_file = self.resolve_snapshot_file(event.snapshot_path)
                status = event.line_crossing_status or "Normal Detection"
                msg = (
                    "SEMANTICEDGE EVIDENCE RECORD\n"
                    "----------------------------------------\n"
                    f"EVENT ID    : {event.id}\n"
                    f"CAMERA      : {event.camera.name}\n"
                    f"OBJECT      : {event.class_name.title()}\n"
                    f"TRACK ID    : #{event.track_id}\n"
                    f"CONFIDENCE  : {int(event.confidence * 100)}%\n"
                    f"TIMESTAMP   : {event.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"STATUS      : {status}\n"
                    f"DESCRIPTION : {event.description or 'Event snapshot record.'}\n"
                    "----------------------------------------"
                )
                result.update({"event": event, "image_path": img_file, "message": msg, "success": True})
            else:
                result["message"] = (
                    "SEMANTICEDGE QUERY RESULT\n"
                    "----------------------------------------\n"
                    f"No detection records found for Event ID {eid}."
                )
            return result

        # ── 3. Latest Intrusion ────────────────────────────────────────────
        if intent == INTENT_LATEST_INTRUSION:
            event = event_qs.filter(line_crossing_status__icontains="intrusion").order_by("-created_at").first()
            if not event:
                event = event_qs.order_by("-created_at").first()

            if event:
                img_file = self.resolve_snapshot_file(event.snapshot_path)
                zone_name = event.line_crossing_status.split(":", 1)[1].strip() if ":" in event.line_crossing_status else event.line_crossing_status
                msg = (
                    "SEMANTICEDGE SURVEILLANCE REPORT\n"
                    "INTRUSION EVENT RECORD\n"
                    "----------------------------------------\n"
                    f"EVENT ID    : {event.id}\n"
                    f"CAMERA      : {event.camera.name}\n"
                    f"ZONE        : {zone_name}\n"
                    f"OBJECT      : {event.class_name.title()}\n"
                    f"TRACK ID    : #{event.track_id}\n"
                    f"CONFIDENCE  : {int(event.confidence * 100)}%\n"
                    f"TIMESTAMP   : {event.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"STATUS      : {event.line_crossing_status}\n"
                    f"DESCRIPTION : {event.description or 'Restricted area breach detected.'}\n"
                    "----------------------------------------"
                )
                result.update({"event": event, "image_path": img_file, "message": msg, "success": True})
            else:
                result["message"] = (
                    "SEMANTICEDGE SURVEILLANCE REPORT\n"
                    "----------------------------------------\n"
                    "No intrusion or detection records found in database."
                )
            return result

        # ── 4. Latest Image / Snapshot ─────────────────────────────────────
        if intent == INTENT_LATEST_IMAGE:
            event = event_qs.order_by("-created_at").first()
            if event:
                img_file = self.resolve_snapshot_file(event.snapshot_path)
                msg = (
                    "SEMANTICEDGE EVIDENCE RECORD\n"
                    "LATEST CAPTURE\n"
                    "----------------------------------------\n"
                    f"EVENT ID    : {event.id}\n"
                    f"CAMERA      : {event.camera.name}\n"
                    f"OBJECT      : {event.class_name.title()}\n"
                    f"TRACK ID    : #{event.track_id}\n"
                    f"CONFIDENCE  : {int(event.confidence * 100)}%\n"
                    f"TIMESTAMP   : {event.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"STATUS      : {event.line_crossing_status}\n"
                    "----------------------------------------"
                )
                result.update({"event": event, "image_path": img_file, "message": msg, "success": True})
            else:
                result["message"] = (
                    "SEMANTICEDGE EVIDENCE RECORD\n"
                    "----------------------------------------\n"
                    "No detection events recorded in database yet."
                )
            return result

        # ── 5. Yesterday Alerts ────────────────────────────────────────────
        if intent == INTENT_YESTERDAY_ALERTS:
            now = timezone.now()
            y_start = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            y_end = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)

            qs = event_qs.filter(created_at__range=(y_start, y_end))
            count = qs.count()
            intrusions_count = qs.filter(line_crossing_status__icontains="intrusion").count()
            top_events = list(qs.order_by("-created_at")[:5])

            if count > 0:
                lines = [
                    "SEMANTICEDGE ALERTS SUMMARY",
                    f"PERIOD      : YESTERDAY ({y_start.strftime('%Y-%m-%d')})",
                    f"TOTAL EVENTS: {count}",
                    f"INTRUSIONS  : {intrusions_count}",
                    "----------------------------------------",
                    "RECENT ENTRIES:",
                ]
                for idx, ev in enumerate(top_events, start=1):
                    lines.append(f"[{idx}] ID={ev.id} | {ev.created_at.strftime('%H:%M:%S')} | {ev.camera.name} | {ev.class_name.title()} #{ev.track_id} | {ev.line_crossing_status}")
                lines.append("----------------------------------------")
                msg = "\n".join(lines)
                first_ev = top_events[0]
                img_file = self.resolve_snapshot_file(first_ev.snapshot_path)
                result.update({"event": first_ev, "image_path": img_file, "message": msg, "success": True})
            else:
                result["message"] = (
                    "SEMANTICEDGE ALERTS SUMMARY\n"
                    "----------------------------------------\n"
                    f"No events or intrusions were recorded yesterday ({y_start.strftime('%Y-%m-%d')})."
                )
            return result

        # ── 6. Filtered Alerts (Date or Camera) ────────────────────────────
        if intent == INTENT_ALERTS_FILTER:
            filter_type = params.get("filter_type")
            if filter_type == "camera":
                cam_name = params.get("camera", "")
                qs = event_qs.filter(camera__name__icontains=cam_name)
                filter_label = f"CAMERA '{cam_name}'"
            else:
                date_val = params.get("date", "today")
                if date_val == "today":
                    now = timezone.now()
                    d_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    d_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                    filter_label = f"TODAY ({d_start.strftime('%Y-%m-%d')})"
                else:
                    try:
                        parsed = datetime.strptime(date_val, "%Y-%m-%d")
                        d_start = timezone.make_aware(parsed.replace(hour=0, minute=0, second=0))
                        d_end = timezone.make_aware(parsed.replace(hour=23, minute=59, second=59))
                        filter_label = date_val
                    except Exception:
                        d_start = timezone.now().replace(hour=0, minute=0, second=0)
                        d_end = timezone.now().replace(hour=23, minute=59, second=59)
                        filter_label = "CURRENT DATE"
                qs = event_qs.filter(created_at__range=(d_start, d_end))

            count = qs.count()
            intrusions_count = qs.filter(line_crossing_status__icontains="intrusion").count()
            top_events = list(qs.order_by("-created_at")[:5])

            if count > 0:
                lines = [
                    "SEMANTICEDGE ALERTS SUMMARY",
                    f"FILTER      : {filter_label}",
                    f"TOTAL EVENTS: {count}",
                    f"INTRUSIONS  : {intrusions_count}",
                    "----------------------------------------",
                    "RECENT ENTRIES:",
                ]
                for idx, ev in enumerate(top_events, start=1):
                    lines.append(f"[{idx}] ID={ev.id} | {ev.created_at.strftime('%H:%M:%S')} | {ev.camera.name} | {ev.class_name.title()} #{ev.track_id} | {ev.line_crossing_status}")
                lines.append("----------------------------------------")
                msg = "\n".join(lines)
                first_ev = top_events[0]
                img_file = self.resolve_snapshot_file(first_ev.snapshot_path)
                result.update({"event": first_ev, "image_path": img_file, "message": msg, "success": True})
            else:
                result["message"] = (
                    "SEMANTICEDGE ALERTS SUMMARY\n"
                    "----------------------------------------\n"
                    f"No events found matching filter: {filter_label}."
                )
            return result

        # ── 7. Camera Fleet / Status ───────────────────────────────────────
        if intent == INTENT_CAMERA_STATUS:
            cams = list(cam_qs.all())
            total = len(cams)
            active_count = sum(1 for c in cams if c.is_active)

            lines = [
                "SEMANTICEDGE CAMERA FLEET STATUS",
                "----------------------------------------",
                f"TOTAL CAMERAS: {total}",
                f"ACTIVE FEEDS : {active_count}",
                "----------------------------------------",
            ]
            for idx, c in enumerate(cams, start=1):
                last_ev = event_qs.filter(camera=c).order_by("-created_at").first()
                last_time = last_ev.created_at.strftime("%Y-%m-%d %H:%M:%S") if last_ev else "None"
                status_str = "ACTIVE" if c.is_active else "INACTIVE"
                lines.append(
                    f"[{idx}] {c.name}\n"
                    f"    Source  : {c.source_url}\n"
                    f"    Status  : {status_str}\n"
                    f"    Mode    : {c.get_scene_mode_display()}\n"
                    f"    Tracking: {'ENABLED' if c.tracker_enabled else 'DISABLED'}\n"
                    f"    Last Evt: {last_time}"
                )
            lines.append("----------------------------------------")
            result.update({"message": "\n".join(lines), "success": True})
            return result

        # ── 8. System Status / Telemetry ───────────────────────────────────
        if intent == INTENT_SYSTEM_STATUS:
            base_dir = Path(getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent))
            media_dir = Path(getattr(settings, "MEDIA_ROOT", base_dir / "media"))
            media_bytes = sum(f.stat().st_size for f in media_dir.glob("**/*") if f.is_file()) if media_dir.is_dir() else 0
            media_mb = media_bytes / (1024 * 1024)

            total_disk, used_disk, free_disk = shutil.disk_usage("/")
            disk_total_gb = total_disk / (1024**3)
            disk_used_gb = used_disk / (1024**3)
            disk_pct = (used_disk / total_disk) * 100

            cpu_pct = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            ram_avail_gb = mem.available / (1024**3)
            ram_total_gb = mem.total / (1024**3)

            total_evs = event_qs.count()
            total_cams = cam_qs.count()
            active_cams = cam_qs.filter(is_active=True).count()
            active_zones = zone_qs.filter(is_active=True).count()

            lines = [
                "SEMANTICEDGE SYSTEM TELEMETRY",
                "----------------------------------------",
                "SERVER STATUS : ONLINE (HEALTHY)",
                f"PLATFORM      : {platform.system()} ({platform.release()})",
                f"CPU USAGE     : {cpu_pct:.1f}%",
                f"RAM USAGE     : {ram_avail_gb:.1f} GB free of {ram_total_gb:.1f} GB",
                f"DISK STORAGE  : {disk_used_gb:.1f} GB / {disk_total_gb:.1f} GB ({disk_pct:.1f}% used)",
                f"MEDIA ARCHIVE : {media_mb:.1f} MB",
                f"DATABASE LOGS : {total_evs} detection events",
                f"CAMERA FLEET  : {active_cams}/{total_cams} feeds active",
                f"MONITOR ZONES : {active_zones} active zones",
                "----------------------------------------",
            ]
            result.update({"message": "\n".join(lines), "success": True})
            return result

        # ── 9. Detection Statistics ────────────────────────────────────────
        if intent == INTENT_STATS:
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            today_qs = event_qs.filter(created_at__gte=today_start)

            total_today = today_qs.count()
            intrusions_today = today_qs.filter(line_crossing_status__icontains="intrusion").count()
            attendance_today = AttendanceRecord.objects.filter(timestamp__gte=today_start).count() if user is None or user.is_staff else AttendanceRecord.objects.filter(user=user, timestamp__gte=today_start).count()

            class_counts = today_qs.values("class_name").annotate(c=Count("id")).order_by("-c")[:5]

            lines = [
                "SEMANTICEDGE DETECTION STATISTICS",
                "----------------------------------------",
                f"PERIOD        : TODAY ({today_start.strftime('%Y-%m-%d')})",
                f"TOTAL EVENTS  : {total_today}",
                f"INTRUSIONS    : {intrusions_today}",
                f"ATTENDANCE    : {attendance_today}",
                "----------------------------------------",
                "CLASSIFICATION BREAKDOWN (TOP):",
            ]
            if class_counts:
                for item in class_counts:
                    lines.append(f"- {item['class_name'].title():<12}: {item['c']} detections")
            else:
                lines.append("- No classifications logged today.")
            lines.append("----------------------------------------")
            result.update({"message": "\n".join(lines), "success": True})
            return result

        # ── 10. Monitoring Zones ───────────────────────────────────────────
        if intent == INTENT_ZONES:
            zones = list(zone_qs.select_related("camera").all())
            lines = [
                "SEMANTICEDGE MONITORING ZONES",
                "----------------------------------------",
                f"CONFIGURED ZONES: {len(zones)}",
                "----------------------------------------",
            ]
            if zones:
                for idx, z in enumerate(zones, start=1):
                    target_str = ", ".join(z.target_classes) if z.target_classes else "all classes"
                    status_str = "ACTIVE" if z.is_active else "INACTIVE"
                    lines.append(
                        f"[{idx}] {z.name}\n"
                        f"    Camera  : {z.camera.name}\n"
                        f"    Type    : {z.get_zone_type_display()}\n"
                        f"    Targets : {target_str}\n"
                        f"    Status  : {status_str}"
                    )
            else:
                lines.append("No active monitoring zones configured.")
            lines.append("----------------------------------------")
            result.update({"message": "\n".join(lines), "success": True})
            return result

        # ── 11. Video / Log Exports ────────────────────────────────────────
        if intent == INTENT_EXPORTS:
            base_dir = Path(getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent))
            exp_dir = base_dir / "media" / "exports"
            files = list(exp_dir.glob("*.mp4")) if exp_dir.is_dir() else []

            lines = [
                "SEMANTICEDGE EXPORT ARCHIVE",
                "----------------------------------------",
                f"AVAILABLE EXPORTS: {len(files)} files",
                "----------------------------------------",
            ]
            if files:
                for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                    size_mb = f.stat().st_size / (1024 * 1024)
                    lines.append(f"- {f.name} ({size_mb:.1f} MB)\n  Format: H.264 / AVC1 (Web-Ready)")
            else:
                lines.append("No video clips currently archived in media/exports/.")
            lines.append("----------------------------------------")
            lines.append("To generate new video or CSV exports, use the NVR web portal at /export/.")
            result.update({"message": "\n".join(lines), "success": True})
            return result

        # ── 12. Help / Capabilities ────────────────────────────────────────
        if intent == INTENT_HELP:
            lines = [
                "SEMANTICEDGE SECURITY ASSISTANT",
                "OPERATIONAL CAPABILITIES",
                "----------------------------------------",
                "SURVEILLANCE OPERATIONS:",
                "- 'latest intrusion'    : View most recent perimeter breach",
                "- 'show latest image'   : View latest captured snapshot",
                "- 'evidence track 5'    : Retrieve snapshot for Track ID #5",
                "- 'event 12'            : Retrieve snapshot for Event ID 12",
                "- 'alerts today'        : Summary of today's detections",
                "- 'yesterday alerts'    : Security events logged yesterday",
                "- 'alerts for Camera 1' : Filter events by camera name",
                "- 'camera status'       : Fleet status and active feeds",
                "- 'system status'       : CPU, RAM, disk, and media storage",
                "- 'detection statistics': Activity breakdown by object class",
                "- 'monitoring zones'    : Active tripwires and restricted areas",
                "- 'export requests'     : Recent video exports and status",
                "----------------------------------------",
                "SESSION COMMANDS:",
                "- /help   : Display this operational guide",
                "- /status : Display current operator session status",
                "- /logout : Terminate current security session",
            ]
            result.update({"message": "\n".join(lines), "success": True})
            return result

        # ── 13. General Conversation / Unsupported Query ───────────────────
        lines = [
            "SEMANTICEDGE SECURITY ASSISTANT",
            "QUERY NOT RECOGNIZED",
            "----------------------------------------",
            "The request could not be matched to an active surveillance operation.",
            "",
            "RECOMMENDED OPERATIONAL QUERIES:",
            "- 'latest intrusion'",
            "- 'alerts today'",
            "- 'camera status'",
            "- 'system status'",
            "- 'today stats'",
            "- 'evidence for track 5'",
            "- 'monitoring zones'",
            "- 'export requests'",
            "----------------------------------------",
            "Send /help for full capabilities or /logout to end session.",
        ]
        result.update({"message": "\n".join(lines), "success": False})
        return result

    def interpret_and_query(self, user_text: str, user: User | None = None) -> dict[str, Any]:
        intent, params = self.nlp_engine.parse_intent(user_text)
        return self.query_sqlite_for_intent(intent, params, user=user)

    def send_photo_response(self, chat_id: str, image_path: Path, caption: str) -> bool:
        if not self.base_url:
            return False
        url = f"{self.base_url}/sendPhoto"
        try:
            with open(image_path, "rb") as photo_file:
                resp = requests.post(
                    url,
                    data={"chat_id": chat_id, "caption": caption},
                    files={"photo": photo_file},
                    timeout=15,
                )
            return resp.ok
        except Exception as exc:
            logger.error(f"[OpenClaw] Failed to send photo to Telegram: {exc}")
            return False

    def send_text_response(self, chat_id: str, text: str) -> bool:
        if not self.base_url:
            return False
        url = f"{self.base_url}/sendMessage"
        try:
            resp = requests.post(
                url,
                json={"chat_id": chat_id, "text": text},
                timeout=8,
            )
            return resp.ok
        except Exception as exc:
            logger.error(f"[OpenClaw] Failed to send message to Telegram: {exc}")
            return False

    def handle_incoming_message(
        self,
        user_text: str,
        chat_id: str | None = None,
        bypass_auth: bool = False,
    ) -> dict[str, Any]:
        """
        End-to-end handler for an incoming Telegram user request.
        Manages authentication state machine, natural-language query execution,
        and post-query feedback recording.
        """
        from nvr.models import TelegramFeedback

        target_chat_id = str(chat_id or self.chat_id)
        raw_text = user_text.strip()
        cleaned_text = raw_text.lower()

        logger.info(f"[TELEGRAM RECEIVE] Message received: '{raw_text}' from chat {target_chat_id}")
        print(f"[TELEGRAM RECEIVE] Message received: '{raw_text}' from chat {target_chat_id}")

        session = self.get_or_create_session(target_chat_id)

        result: dict[str, Any] = {
            "success": False,
            "intent": "",
            "message": "",
            "event": None,
            "image_path": None,
            "send_success": False,
        }

        # ─────────────────────────────────────────────────────────────────
        # STEP 1: AUTHENTICATION FLOW (If not authenticated)
        # ─────────────────────────────────────────────────────────────────
        if not bypass_auth and not session.is_authenticated:
            # Check for direct one-line /login <username> <password>
            if cleaned_text.startswith("/login"):
                parts = raw_text.split(maxsplit=2)
                if len(parts) == 3:
                    u_cand, p_cand = parts[1], parts[2]
                    authenticated_user = authenticate(username=u_cand, password=p_cand)
                    if authenticated_user and authenticated_user.is_active:
                        session.user = authenticated_user
                        session.is_authenticated = True
                        session.state = "AUTHENTICATED_IDLE"
                        session.pending_username = ""
                        session.save()
                        role = "Administrator" if authenticated_user.is_staff else "Security Operator"
                        msg = (
                            "SEMANTICEDGE SECURITY ASSISTANT\n"
                            "SESSION ESTABLISHED\n"
                            "----------------------------------------\n"
                            f"OPERATOR  : {authenticated_user.username}\n"
                            f"ROLE      : {role}\n"
                            f"STATUS    : Connected\n"
                            "----------------------------------------\n"
                            f"Welcome, {authenticated_user.username}. SemanticEdge Surveillance Assistant is initialized.\n\n"
                            "CAPABILITIES & SAMPLE QUERIES:\n"
                            "- Latest Intrusion : 'latest intrusion', 'recent breach'\n"
                            "- Filtered Alerts  : 'alerts today', 'alerts for Camera 1'\n"
                            "- Target Evidence  : 'evidence for track 5', 'event 102'\n"
                            "- Camera Fleet     : 'camera status', 'active cameras'\n"
                            "- Telemetry/Health : 'system status', 'storage usage'\n"
                            "- Analytics & Stats: 'detection statistics', 'today stats'\n"
                            "- Monitoring Zones : 'monitoring zones', 'tripwires'\n"
                            "- Evidence Exports : 'export requests', 'recent exports'\n"
                            "- Session Control  : /help, /status, /logout\n\n"
                            "Type an operational request to query the NVR."
                        )
                        self.send_text_response(target_chat_id, msg)
                        result.update({"success": True, "intent": INTENT_LOGIN, "message": msg, "send_success": True})
                        return result
                    else:
                        msg = (
                            "SEMANTICEDGE SECURITY SYSTEM\n"
                            "AUTHENTICATION FAILED\n"
                            "----------------------------------------\n"
                            "Invalid credentials provided.\n"
                            "Please enter your username to try again:"
                        )
                        session.state = "AWAITING_USERNAME"
                        session.save()
                        self.send_text_response(target_chat_id, msg)
                        result.update({"success": False, "intent": INTENT_LOGIN, "message": msg, "send_success": True})
                        return result

            # Interactive state machine for login
            if session.state == "AWAITING_USERNAME":
                candidate_username = raw_text
                user_exists = User.objects.filter(username=candidate_username).exists()
                if user_exists:
                    session.pending_username = candidate_username
                    session.state = "AWAITING_PASSWORD"
                    session.save()
                    msg = (
                        "SEMANTICEDGE SECURITY SYSTEM\n"
                        "AUTHENTICATION IN PROGRESS\n"
                        "----------------------------------------\n"
                        f"Username: {candidate_username}\n"
                        "Please enter your password:"
                    )
                else:
                    msg = (
                        "SEMANTICEDGE SECURITY SYSTEM\n"
                        "AUTHENTICATION FAILED\n"
                        "----------------------------------------\n"
                        f"User '{candidate_username}' not found in NVR database.\n"
                        "Please enter a valid username:"
                    )
                self.send_text_response(target_chat_id, msg)
                result.update({"success": False, "intent": INTENT_LOGIN, "message": msg, "send_success": True})
                return result

            if session.state == "AWAITING_PASSWORD":
                password_cand = raw_text
                authenticated_user = authenticate(username=session.pending_username, password=password_cand)
                if authenticated_user and authenticated_user.is_active:
                    session.user = authenticated_user
                    session.is_authenticated = True
                    session.state = "AUTHENTICATED_IDLE"
                    session.pending_username = ""
                    session.save()
                    role = "Administrator" if authenticated_user.is_staff else "Security Operator"
                    msg = (
                        "SEMANTICEDGE SECURITY ASSISTANT\n"
                        "SESSION ESTABLISHED\n"
                        "----------------------------------------\n"
                        f"OPERATOR  : {authenticated_user.username}\n"
                        f"ROLE      : {role}\n"
                        f"STATUS    : Connected\n"
                        "----------------------------------------\n"
                        f"Welcome, {authenticated_user.username}. SemanticEdge Surveillance Assistant is initialized.\n\n"
                        "CAPABILITIES & SAMPLE QUERIES:\n"
                        "- Latest Intrusion : 'latest intrusion', 'recent breach'\n"
                        "- Filtered Alerts  : 'alerts today', 'alerts for Camera 1'\n"
                        "- Target Evidence  : 'evidence for track 5', 'event 102'\n"
                        "- Camera Fleet     : 'camera status', 'active cameras'\n"
                        "- Telemetry/Health : 'system status', 'storage usage'\n"
                        "- Analytics & Stats: 'detection statistics', 'today stats'\n"
                        "- Monitoring Zones : 'monitoring zones', 'tripwires'\n"
                        "- Evidence Exports : 'export requests', 'recent exports'\n"
                        "- Session Control  : /help, /status, /logout\n\n"
                        "Type an operational request to query the NVR."
                    )
                    self.send_text_response(target_chat_id, msg)
                    result.update({"success": True, "intent": INTENT_LOGIN, "message": msg, "send_success": True})
                    return result
                else:
                    session.state = "AWAITING_USERNAME"
                    session.pending_username = ""
                    session.save()
                    msg = (
                        "SEMANTICEDGE SECURITY SYSTEM\n"
                        "AUTHENTICATION FAILED\n"
                        "----------------------------------------\n"
                        "Invalid password for the specified user.\n"
                        "Please enter your username to try again:"
                    )
                    self.send_text_response(target_chat_id, msg)
                    result.update({"success": False, "intent": INTENT_LOGIN, "message": msg, "send_success": True})
                    return result

            # Unauthenticated and in IDLE or general command -> Prompt for login
            session.state = "AWAITING_USERNAME"
            session.save()
            msg = (
                "SEMANTICEDGE SECURITY SYSTEM\n"
                "AUTHENTICATION REQUIRED\n"
                "----------------------------------------\n"
                "Access to surveillance operations is restricted.\n"
                "Please enter your NVR username to authenticate:"
            )
            self.send_text_response(target_chat_id, msg)
            result.update({"success": False, "intent": INTENT_LOGIN, "message": msg, "send_success": True})
            return result

        # ─────────────────────────────────────────────────────────────────
        # STEP 2: LOGOUT COMMAND
        # ─────────────────────────────────────────────────────────────────
        if cleaned_text in ["/logout", "logout", "sign out"]:
            session.is_authenticated = False
            session.user = None
            session.state = "IDLE"
            session.pending_username = ""
            session.save()
            msg = (
                "SEMANTICEDGE SECURITY SYSTEM\n"
                "SESSION TERMINATED\n"
                "----------------------------------------\n"
                "User logged out successfully.\n"
                "Send /start or /login to begin a new session."
            )
            self.send_text_response(target_chat_id, msg)
            result.update({"success": True, "intent": INTENT_LOGOUT, "message": msg, "send_success": True})
            return result

        # ─────────────────────────────────────────────────────────────────
        # STEP 3: FEEDBACK COLLECTION (If user responds YES/NO to prompt)
        # ─────────────────────────────────────────────────────────────────
        if (
            session.state == "AWAITING_FEEDBACK"
            and cleaned_text in ["yes", "y", "no", "n", "helpful", "unhelpful", "good", "bad"]
        ):
            is_helpful = cleaned_text in ["yes", "y", "helpful", "good"]
            TelegramFeedback.objects.create(
                session=session,
                user=session.user,
                chat_id=target_chat_id,
                query_text=session.last_query,
                intent=session.last_intent,
                is_helpful=is_helpful,
                raw_feedback=cleaned_text,
            )
            session.state = "AUTHENTICATED_IDLE"
            session.save()
            msg = (
                "SEMANTICEDGE SECURITY ASSISTANT\n"
                "FEEDBACK RECORDED\n"
                "----------------------------------------\n"
                "Thank you for your feedback. System telemetry updated."
            )
            self.send_text_response(target_chat_id, msg)
            result.update({"success": True, "intent": INTENT_FEEDBACK, "message": msg, "send_success": True})
            return result

        # ─────────────────────────────────────────────────────────────────
        # STEP 4: OPERATIONAL SURVEILLANCE QUERIES
        # ─────────────────────────────────────────────────────────────────
        session.last_query = raw_text

        # Stage 2: Intent parsed by OpenClaw
        intent, params = self.nlp_engine.parse_intent(raw_text)
        session.last_intent = intent
        logger.info(f"[OPENCLAW NLP] Intent parsed: intent='{intent}', params={params}")
        print(f"[OPENCLAW NLP] Intent parsed: intent='{intent}', params={params}")

        # Stage 3 & 4: SQLite query executed & DetectionEvent found
        query_res = self.query_sqlite_for_intent(intent, params, user=session.user)
        event = query_res.get("event")
        image_path = query_res.get("image_path")
        msg = query_res.get("message", "")
        success = query_res.get("success", False)

        # Stage 5: Snapshot loaded
        if image_path and image_path.is_file():
            size_bytes = image_path.stat().st_size
            logger.info(f"[SNAPSHOT LOAD] Snapshot loaded: path='{image_path}', exists=True, size={size_bytes} bytes")
            print(f"[SNAPSHOT LOAD] Snapshot loaded: path='{image_path}', exists=True, size={size_bytes} bytes")
        else:
            path_str = str(image_path) if image_path else (event.snapshot_path if event else "None")
            logger.info(f"[SNAPSHOT LOAD] Snapshot loaded: path='{path_str}', exists=False, size=0 bytes")
            print(f"[SNAPSHOT LOAD] Snapshot loaded: path='{path_str}', exists=False, size=0 bytes")

        # Stage 6: Telegram response sent
        send_success = False
        resp_type = "none"

        # Ask feedback if operational query was served successfully
        ask_feedback = success and intent not in [INTENT_HELP, INTENT_LOGOUT, INTENT_FEEDBACK]

        if target_chat_id and self.bot_token:
            if event and image_path and image_path.is_file():
                resp_type = "photo"
                caption = msg
                if ask_feedback:
                    caption += "\n\nWas this information helpful? (Reply YES or NO)"
                send_success = self.send_photo_response(target_chat_id, image_path, caption)
            else:
                resp_type = "text"
                full_text = msg
                if ask_feedback:
                    full_text += "\n\nWas this information helpful? (Reply YES or NO)"
                send_success = self.send_text_response(target_chat_id, full_text)

            logger.info(f"[TELEGRAM SEND] Response sent: type='{resp_type}', chat='{target_chat_id}', success={send_success}")
            print(f"[TELEGRAM SEND] Response sent: type='{resp_type}', chat='{target_chat_id}', success={send_success}")

        if ask_feedback:
            session.state = "AWAITING_FEEDBACK"
        else:
            session.state = "AUTHENTICATED_IDLE"
        session.save()

        result.update({
            "event": event,
            "image_path": image_path,
            "message": msg,
            "success": success,
            "intent": intent,
            "send_success": send_success,
        })
        return result
