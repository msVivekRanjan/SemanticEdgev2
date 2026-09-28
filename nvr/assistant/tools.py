"""
nvr/assistant/tools.py
----------------------
Controlled server-side NVR tools for the SemanticEdge Internal Assistant.
All access to detection data, cameras, system health, and snapshots is strictly
channeled through these functions. The LLM NEVER directly queries the database
or generates arbitrary SQL.
"""

from __future__ import annotations

import logging
import os
import platform
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import psutil
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone

logger = logging.getLogger("semanticedge.assistant.tools")


class NVRTools:
    """
    Controlled toolkit providing high-level, read-only SemanticEdge NVR operations.
    Scoped per requesting user unless user is staff/superuser.
    """

    @staticmethod
    def resolve_snapshot_file(snapshot_rel_path: str) -> Optional[Path]:
        """
        Locates the snapshot image file on disk from its relative database path.
        """
        if not snapshot_rel_path:
            return None

        clean_rel = snapshot_rel_path.lstrip("/")
        if clean_rel.startswith("media/"):
            clean_rel = clean_rel[len("media/"):]

        media_root = Path(getattr(settings, "MEDIA_ROOT", Path(__file__).resolve().parent.parent.parent / "media"))
        candidate = media_root / clean_rel
        if candidate.is_file():
            return candidate

        base_dir = Path(getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent.parent))
        candidate2 = base_dir / snapshot_rel_path.lstrip("/")
        if candidate2.is_file():
            return candidate2

        direct = Path(snapshot_rel_path)
        if direct.is_file():
            return direct

        return None

    @classmethod
    def get_event_queryset(cls, user: Optional[User] = None):
        from nvr.models import DetectionEvent

        qs = DetectionEvent.objects.select_related("camera", "user")
        if user and not (user.is_staff or user.is_superuser):
            qs = qs.filter(Q(user=user) | Q(camera__owner=user))
        return qs

    @classmethod
    def get_camera_queryset(cls, user: Optional[User] = None):
        from nvr.models import Camera

        qs = Camera.objects.all()
        if user and not (user.is_staff or user.is_superuser):
            qs = qs.filter(owner=user)
        return qs

    @classmethod
    def get_zone_queryset(cls, user: Optional[User] = None):
        from nvr.models import MonitoringZone

        qs = MonitoringZone.objects.select_related("camera")
        if user and not (user.is_staff or user.is_superuser):
            qs = qs.filter(camera__owner=user)
        return qs

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Alert & Detection Details
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_alert_details(cls, event_id: int, user: Optional[User] = None) -> dict[str, Any]:
        """
        Retrieve structured details for an alert/event by ID.
        """
        qs = cls.get_event_queryset(user)
        event = qs.filter(id=event_id).first()
        if not event:
            return {"found": False, "error": f"Alert/Event #{event_id} not found or permission denied."}

        disk_file = cls.resolve_snapshot_file(event.snapshot_path)
        return {
            "found": True,
            "id": event.id,
            "camera_id": event.camera.id,
            "camera_name": event.camera.name,
            "track_id": event.track_id,
            "class_name": event.class_name,
            "confidence": round(event.confidence, 4),
            "confidence_pct": f"{int(event.confidence * 100)}%",
            "line_crossing_status": event.line_crossing_status,
            "description": event.description or "",
            "timestamp": event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "snapshot_url": event.snapshot_path,
            "snapshot_exists": bool(disk_file and disk_file.is_file()),
            "bbox": [event.bbox_x1, event.bbox_y1, event.bbox_x2, event.bbox_y2],
            "frame_number": event.frame_number,
        }

    @classmethod
    def get_latest_intrusion(cls, user: Optional[User] = None) -> dict[str, Any]:
        """
        Find the most recent perimeter breach or intrusion event.
        """
        qs = cls.get_event_queryset(user)
        event = qs.filter(line_crossing_status__icontains="intrusion").order_by("-created_at").first()
        if not event:
            # Fallback to the latest event overall
            event = qs.order_by("-created_at").first()

        if not event:
            return {"found": False, "message": "No detection or intrusion events recorded in database."}

        return cls.get_alert_details(event.id, user)

    @classmethod
    def get_latest_image(cls, user: Optional[User] = None) -> dict[str, Any]:
        """
        Retrieve the latest captured image snapshot from the NVR.
        """
        qs = cls.get_event_queryset(user)
        event = qs.order_by("-created_at").first()
        if not event:
            return {"found": False, "message": "No detection events recorded in database yet."}
        return cls.get_alert_details(event.id, user)

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Track Information & Trajectory History
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_track_history(
        cls,
        track_id: int,
        camera_id: Optional[int] = None,
        limit: int = 15,
        user: Optional[User] = None,
    ) -> dict[str, Any]:
        """
        Retrieve the chronological movement history of a tracked object (track_id).
        """
        qs = cls.get_event_queryset(user).filter(track_id=track_id)
        if camera_id:
            qs = qs.filter(camera_id=camera_id)

        events = list(qs.order_by("-created_at")[:limit])
        if not events:
            return {
                "found": False,
                "track_id": track_id,
                "message": f"No detection records found for Track #{track_id}.",
                "history": [],
            }

        history = []
        for e in events:
            disk_file = cls.resolve_snapshot_file(e.snapshot_path)
            history.append({
                "event_id": e.id,
                "camera_name": e.camera.name,
                "camera_id": e.camera.id,
                "class_name": e.class_name,
                "timestamp": e.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "status": e.line_crossing_status,
                "confidence": round(e.confidence, 4),
                "snapshot_url": e.snapshot_path,
                "snapshot_exists": bool(disk_file and disk_file.is_file()),
                "bbox": [e.bbox_x1, e.bbox_y1, e.bbox_x2, e.bbox_y2],
            })

        latest = events[0]
        latest_file = cls.resolve_snapshot_file(latest.snapshot_path)

        return {
            "found": True,
            "track_id": track_id,
            "class_name": latest.class_name,
            "total_records": len(history),
            "latest_event_id": latest.id,
            "latest_camera": latest.camera.name,
            "latest_timestamp": latest.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "snapshot_url": latest.snapshot_path,
            "snapshot_exists": bool(latest_file and latest_file.is_file()),
            "history": history,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Related Detections & Temporal Proximity
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_related_detections(
        cls,
        event_id: int,
        window_seconds: int = 120,
        user: Optional[User] = None,
    ) -> dict[str, Any]:
        """
        Find detections that occurred around the same time as a given event (temporal co-occurrence).
        """
        qs = cls.get_event_queryset(user)
        ref_event = qs.filter(id=event_id).first()
        if not ref_event:
            return {"found": False, "error": f"Event #{event_id} not found."}

        t_start = ref_event.created_at - timedelta(seconds=window_seconds)
        t_end = ref_event.created_at + timedelta(seconds=window_seconds)

        related_qs = qs.filter(created_at__range=(t_start, t_end)).exclude(id=event_id).order_by("created_at")[:20]

        items = []
        for e in related_qs:
            disk_file = cls.resolve_snapshot_file(e.snapshot_path)
            items.append({
                "id": e.id,
                "camera_name": e.camera.name,
                "class_name": e.class_name,
                "track_id": e.track_id,
                "confidence_pct": f"{int(e.confidence * 100)}%",
                "status": e.line_crossing_status,
                "timestamp": e.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "time_diff_seconds": round((e.created_at - ref_event.created_at).total_seconds(), 1),
                "snapshot_url": e.snapshot_path,
                "snapshot_exists": bool(disk_file and disk_file.is_file()),
            })

        return {
            "found": True,
            "reference_event_id": ref_event.id,
            "reference_timestamp": ref_event.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "window_seconds": window_seconds,
            "related_count": len(items),
            "related_detections": items,
        }

    @classmethod
    def get_events_around_timestamp(
        cls,
        timestamp_str: str,
        window_minutes: int = 15,
        camera_name_or_id: Optional[str] = None,
        user: Optional[User] = None,
    ) -> dict[str, Any]:
        """
        Query detections within a time window of a specified timestamp.
        """
        qs = cls.get_event_queryset(user)
        try:
            # Parse multiple common formats
            cleaned_ts = timestamp_str.replace("T", " ").strip()
            if len(cleaned_ts) == 10:  # YYYY-MM-DD
                dt = datetime.strptime(cleaned_ts, "%Y-%m-%d")
                t_start = timezone.make_aware(dt.replace(hour=0, minute=0, second=0))
                t_end = timezone.make_aware(dt.replace(hour=23, minute=59, second=59))
            elif len(cleaned_ts) == 16:  # YYYY-MM-DD HH:MM
                dt = datetime.strptime(cleaned_ts, "%Y-%m-%d %H:%M")
                aware_dt = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                t_start = aware_dt - timedelta(minutes=window_minutes)
                t_end = aware_dt + timedelta(minutes=window_minutes)
            else:
                dt = datetime.strptime(cleaned_ts[:19], "%Y-%m-%d %H:%M:%S")
                aware_dt = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                t_start = aware_dt - timedelta(minutes=window_minutes)
                t_end = aware_dt + timedelta(minutes=window_minutes)
        except Exception as e:
            return {"found": False, "error": f"Invalid timestamp '{timestamp_str}': {e}"}

        filtered = qs.filter(created_at__range=(t_start, t_end))
        if camera_name_or_id:
            if camera_name_or_id.isdigit():
                filtered = filtered.filter(camera_id=int(camera_name_or_id))
            else:
                filtered = filtered.filter(camera__name__icontains=camera_name_or_id)

        events = list(filtered.order_by("-created_at")[:25])
        items = []
        for e in events:
            disk_file = cls.resolve_snapshot_file(e.snapshot_path)
            items.append({
                "id": e.id,
                "camera_name": e.camera.name,
                "class_name": e.class_name,
                "track_id": e.track_id,
                "confidence_pct": f"{int(e.confidence * 100)}%",
                "status": e.line_crossing_status,
                "timestamp": e.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "snapshot_url": e.snapshot_path,
                "snapshot_exists": bool(disk_file and disk_file.is_file()),
            })

        return {
            "found": True,
            "period_start": t_start.strftime("%Y-%m-%d %H:%M:%S"),
            "period_end": t_end.strftime("%Y-%m-%d %H:%M:%S"),
            "count": len(items),
            "events": items,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Camera Fleet & Status
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_camera_status(cls, user: Optional[User] = None) -> dict[str, Any]:
        """
        Retrieve fleet status and telemetry for all active and configured cameras.
        """
        cams = list(cls.get_camera_queryset(user).all())
        event_qs = cls.get_event_queryset(user)

        camera_list = []
        for c in cams:
            last_ev = event_qs.filter(camera=c).order_by("-created_at").first()
            camera_list.append({
                "id": c.id,
                "name": c.name,
                "source_url": c.source_url,
                "is_active": c.is_active,
                "status": "ONLINE" if c.is_active else "OFFLINE",
                "scene_mode": c.get_scene_mode_display(),
                "tracker_enabled": c.tracker_enabled,
                "last_event_time": last_ev.created_at.strftime("%Y-%m-%d %H:%M:%S") if last_ev else None,
                "last_event_class": last_ev.class_name if last_ev else None,
            })

        return {
            "total_cameras": len(cams),
            "active_cameras": sum(1 for c in cams if c.is_active),
            "cameras": camera_list,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 5. System Health, Storage & Telemetry
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_system_telemetry(cls, user: Optional[User] = None) -> dict[str, Any]:
        """
        Retrieve server system metrics: CPU, RAM, disk storage, and archive sizes.
        """
        base_dir = Path(getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent.parent))
        media_dir = Path(getattr(settings, "MEDIA_ROOT", base_dir / "media"))
        media_bytes = sum(f.stat().st_size for f in media_dir.glob("**/*") if f.is_file()) if media_dir.is_dir() else 0
        media_mb = media_bytes / (1024 * 1024)

        try:
            total_disk, used_disk, free_disk = shutil.disk_usage("/")
            disk_total_gb = total_disk / (1024**3)
            disk_used_gb = used_disk / (1024**3)
            disk_pct = (used_disk / total_disk) * 100
        except Exception:
            disk_total_gb = disk_used_gb = disk_pct = 0.0

        try:
            cpu_pct = psutil.cpu_percent(interval=0.05)
            mem = psutil.virtual_memory()
            ram_avail_gb = mem.available / (1024**3)
            ram_total_gb = mem.total / (1024**3)
        except Exception:
            cpu_pct = 0.0
            ram_avail_gb = ram_total_gb = 0.0

        total_evs = cls.get_event_queryset(user).count()
        cam_qs = cls.get_camera_queryset(user)
        total_cams = cam_qs.count()
        active_cams = cam_qs.filter(is_active=True).count()
        active_zones = cls.get_zone_queryset(user).filter(is_active=True).count()

        return {
            "server_status": "ONLINE (HEALTHY)",
            "platform": f"{platform.system()} {platform.release()}",
            "cpu_percent": round(cpu_pct, 1),
            "ram_used_gb": round(ram_total_gb - ram_avail_gb, 2),
            "ram_total_gb": round(ram_total_gb, 2),
            "disk_used_gb": round(disk_used_gb, 1),
            "disk_total_gb": round(disk_total_gb, 1),
            "disk_percent": round(disk_pct, 1),
            "media_archive_mb": round(media_mb, 1),
            "detection_events_logged": total_evs,
            "cameras_active": f"{active_cams}/{total_cams}",
            "active_monitoring_zones": active_zones,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Detection Statistics & Analytics
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_detection_statistics(cls, date_str: str = "today", user: Optional[User] = None) -> dict[str, Any]:
        """
        Retrieve detection statistics, intrusion counts, and class breakdown for a given period.
        """
        from nvr.models import AttendanceRecord

        event_qs = cls.get_event_queryset(user)
        now = timezone.now()

        if date_str == "yesterday":
            start_dt = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
            period_label = f"Yesterday ({start_dt.strftime('%Y-%m-%d')})"
        elif date_str == "today":
            start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_dt = now.replace(hour=23, minute=59, second=59, microsecond=999999)
            period_label = f"Today ({start_dt.strftime('%Y-%m-%d')})"
        else:
            try:
                parsed = datetime.strptime(date_str, "%Y-%m-%d")
                start_dt = timezone.make_aware(parsed.replace(hour=0, minute=0, second=0))
                end_dt = timezone.make_aware(parsed.replace(hour=23, minute=59, second=59))
                period_label = date_str
            except Exception:
                start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_dt = now
                period_label = "Current Date"

        filtered_qs = event_qs.filter(created_at__range=(start_dt, end_dt))
        total_events = filtered_qs.count()
        intrusions = filtered_qs.filter(line_crossing_status__icontains="intrusion").count()

        att_qs = AttendanceRecord.objects.all()
        if user and not (user.is_staff or user.is_superuser):
            att_qs = att_qs.filter(user=user)
        attendance = att_qs.filter(timestamp__range=(start_dt, end_dt)).count()

        class_counts = list(
            filtered_qs.values("class_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:8]
        )

        top_events = []
        for e in filtered_qs.order_by("-created_at")[:5]:
            top_events.append({
                "id": e.id,
                "timestamp": e.created_at.strftime("%H:%M:%S"),
                "camera": e.camera.name,
                "class": e.class_name,
                "track_id": e.track_id,
                "status": e.line_crossing_status,
                "snapshot_url": e.snapshot_path,
            })

        return {
            "period": period_label,
            "total_events": total_events,
            "intrusions": intrusions,
            "attendance": attendance,
            "class_breakdown": {c["class_name"]: c["count"] for c in class_counts},
            "recent_events": top_events,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 7. Monitoring Zones
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_monitoring_zones(cls, user: Optional[User] = None) -> dict[str, Any]:
        """
        List all configured restricted areas and tripwires.
        """
        zones = list(cls.get_zone_queryset(user).all())
        zone_list = []
        for z in zones:
            zone_list.append({
                "id": z.id,
                "name": z.name,
                "camera_name": z.camera.name,
                "camera_id": z.camera.id,
                "zone_type": z.get_zone_type_display(),
                "target_classes": z.target_classes or ["all"],
                "is_active": z.is_active,
            })

        return {
            "total_zones": len(zones),
            "zones": zone_list,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 8. Video and Log Exports
    # ──────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_export_records(cls, user: Optional[User] = None) -> dict[str, Any]:
        """
        Retrieve recently generated video clips and log export files.
        """
        base_dir = Path(getattr(settings, "BASE_DIR", Path(__file__).resolve().parent.parent.parent))
        exp_dir = base_dir / "media" / "exports"
        files = list(exp_dir.glob("*.mp4")) if exp_dir.is_dir() else []

        sorted_files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:6]
        items = []
        for f in sorted_files:
            items.append({
                "filename": f.name,
                "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
                "url": f"/media/exports/{f.name}",
                "format": "H.264 / AVC1 (Web-Ready)",
            })

        return {
            "total_files": len(files),
            "recent_exports": items,
        }
