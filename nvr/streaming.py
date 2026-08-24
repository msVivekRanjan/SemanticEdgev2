"""
nvr/streaming.py
----------------
The integration layer between Django and the YOLOv8+ByteTrack detection pipeline.

Design rules
------------
* Imports directly from semanticedge/src/ package.
* Wraps YOLOv8 + ByteTrack pipeline into an MJPEG frame generator for StreamingHttpResponse.
* Robust video capture handling: supports webcam indexes on macOS (AVFoundation)
  and Linux (V4L2) without forcing FFMPEG on device indexes, as well as RTSP streams.
* Automatically records snapshot previews of detection events for the Review & Explore tabs.
"""

from __future__ import annotations

import os
import sys
import time
import threading
from pathlib import Path
from typing import Generator, TYPE_CHECKING

import cv2

# Ensure semanticedge directory is in sys.path
_SE_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _SE_DIR.parent
if str(_SE_DIR) not in sys.path:
    sys.path.insert(0, str(_SE_DIR))

from src.detector import Detector
from src.tracker import Tracker
from src.trajectory import TrajectoryStore
from src.draw_utils import draw_box, draw_fps
from src import logger as csv_logger

if TYPE_CHECKING:
    from nvr.models import Camera

# ── Module-level stats store ──────────────────────────────────────────────────
_stats_lock = threading.Lock()
_stats: dict[int, dict] = {}
_latest_frames: dict[int, bytes] = {}


def get_stats(camera_id: int) -> dict:
    """Return the latest stats dict for a camera (thread-safe)."""
    with _stats_lock:
        return _stats.get(camera_id, {
            "fps": 0.0,
            "total_objects": 0,
            "track_ids": [],
            "counts": {},
            "is_streaming": False,
        }).copy()


def get_all_active_stats() -> dict[int, dict]:
    """Return stats for all currently active streams."""
    with _stats_lock:
        return {k: v.copy() for k, v in _stats.items()}


def _update_stats(camera_id: int, fps: float, objects: list) -> None:
    """Update the shared stats dict from within the generator thread."""
    counts: dict[str, int] = {}
    track_ids: list[int] = []
    for obj in objects:
        cls = obj["cls_name"]
        counts[cls] = counts.get(cls, 0) + 1
        tid = obj.get("track_id", -1)
        if tid >= 0:
            track_ids.append(tid)

    with _stats_lock:
        _stats[camera_id] = {
            "fps": round(fps, 1),
            "total_objects": len(objects),
            "track_ids": sorted(set(track_ids)),
            "counts": counts,
            "is_streaming": True,
        }


def _center(bbox: list) -> tuple:
    x1, y1, x2, y2 = bbox
    return int((x1 + x2) / 2), int((y1 + y2) / 2)


def _open_capture(source_str: str) -> cv2.VideoCapture | None:
    """
    Open VideoCapture with intelligent platform backend selection.
    Handles numeric webcam indices (e.g. 0, 1) and RTSP URLs / video files.
    """
    source_str = source_str.strip()
    is_index = source_str.isdigit()

    if is_index:
        idx = int(source_str)
        # For index devices, standard default backend (e.g. AVFoundation on Mac, V4L2 on Linux)
        cap = cv2.VideoCapture(idx)
        if not cap.isOpened() and idx != 0:
            # Fallback to index 0 (default built-in camera) if requested index fails
            print(f"[SemanticEdge] Source index {idx} failed to open, trying default webcam (0)...")
            cap = cv2.VideoCapture(0)
        return cap if cap.isOpened() else None

    # For RTSP streams or video files
    cap = cv2.VideoCapture(source_str, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        cap = cv2.VideoCapture(source_str)
    return cap if cap.isOpened() else None


# ── Frame generator ───────────────────────────────────────────────────────────

def frame_generator(camera: "Camera") -> Generator[bytes, None, None]:
    """
    Generator that processes video input with YOLOv8 + ByteTrack
    and yields JPEG bytes for HTTP MJPEG streaming.
    """
    from django.conf import settings

    # Resolve model path & parameters
    model_path = getattr(settings, "YOLO_MODEL_PATH", str(_REPO_ROOT / "yolov8n.pt"))
    conf_threshold = getattr(settings, "YOLO_CONF_THRESHOLD", 0.40)
    device = getattr(settings, "YOLO_DEVICE", "cpu")

    # Initialise CSV logger
    log_dir = _SE_DIR / "output" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = str(log_dir / f"camera_{camera.pk}_detection_log.csv")
    csv_logger.init_logger(log_path)

    # Initialise snapshots directory for Review and Explore tabs
    snapshots_dir = _SE_DIR / "media" / "snapshots" / f"camera_{camera.pk}"
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    # Initialise model
    use_tracking = camera.tracker_enabled
    if use_tracking:
        model = Tracker(
            model_path=model_path,
            conf_threshold=conf_threshold,
            device=device,
        )
    else:
        model = Detector(
            model_path=model_path,
            conf_threshold=conf_threshold,
            device=device,
        )

    # Open video source with robust fallback
    cap = _open_capture(camera.source_url)

    if cap is None:
        print(f"[SemanticEdge] ERROR: Cannot open source '{camera.source_url}' for camera {camera.pk}")
        # Yield a single informative placeholder image frame
        placeholder = cv2.putText(
            (cv2.Mat.zeros(480, 640, cv2.CV_8UC3) if hasattr(cv2, 'Mat') else (cv2.imread(None) or cv2.multiply(cv2.UMat(), 0) if False else None)),
            "CAMERA OFFLINE / SOURCE UNAVAILABLE",
            (40, 240),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 0, 255),
            2
        ) if False else None
        return

    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    # Trajectory store
    traj = TrajectoryStore(max_len=30)

    frame_number = 0
    prev_time = time.perf_counter()
    last_snapshot_time = 0.0

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame_number += 1

            # Run detection / tracking
            if use_tracking:
                objects = model.track(frame)
            else:
                raw = model.detect(frame)
                objects = [{**d, "track_id": -1} for d in raw]

            # Update trajectories
            active_ids: set[int] = set()
            for obj in objects:
                tid = obj["track_id"]
                if tid >= 0:
                    cx, cy = _center(obj["bbox"])
                    traj.update(tid, (cx, cy))
                    active_ids.add(tid)
            traj.purge(active_ids)

            # Draw trajectories behind boxes
            traj.draw(frame)

            # Draw boxes and log entries
            for obj in objects:
                tid = obj["track_id"]
                cx, cy = _center(obj["bbox"])

                draw_box(frame, obj["bbox"], tid, obj["cls_name"], obj["conf"])

                csv_logger.log_entry(
                    frame_number=frame_number,
                    track_id=tid,
                    cls_name=obj["cls_name"],
                    confidence=obj["conf"],
                    bbox=obj["bbox"],
                    center=(cx, cy),
                )

            # Periodic snapshot generation for Review/Explore tabs when objects detected
            current_time = time.time()
            if objects and (current_time - last_snapshot_time > 2.0):
                last_snapshot_time = current_time
                try:
                    snap_path = str(snapshots_dir / f"snap_{frame_number}.jpg")
                    cv2.imwrite(snap_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                except Exception:
                    pass

            # FPS overlay
            now = time.perf_counter()
            fps = 1.0 / (now - prev_time + 1e-9)
            prev_time = now
            draw_fps(frame, fps)

            # Update telemetry stats
            _update_stats(camera.pk, fps, objects)

            # Encode to JPEG
            ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ok:
                continue

            jpeg_bytes = buffer.tobytes()
            with _stats_lock:
                _latest_frames[camera.pk] = jpeg_bytes

            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n"
                + jpeg_bytes
                + b"\r\n"
            )

    except GeneratorExit:
        pass
    finally:
        cap.release()
        with _stats_lock:
            if camera.pk in _stats:
                _stats[camera.pk]["is_streaming"] = False
