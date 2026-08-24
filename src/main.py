"""
main.py
-------
Real-Time Vehicle and Person Detection System
Entry point.  Reads frames from a webcam (or video file), runs
YOLOv8 + ByteTrack, draws trajectories, and logs detections to CSV.

Usage
-----
# Webcam (device 0)
    python src/main.py

# Video file
    python src/main.py --source path/to/video.mp4

# Save output video
    python src/main.py --save-video

# Detection only (no tracking)
    python src/main.py --no-track

# Custom log path
    python src/main.py --log detection_log.csv
"""


from __future__ import annotations

# from openpyxl.workbook import smart_tags
import argparse
import sys
import time
from pathlib import Path

import cv2

# ── local modules ─────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.detector import Detector
from src.tracker import Tracker
from src.trajectory import TrajectoryStore
from src.draw_utils import draw_box, draw_fps
from src import logger as csv_logger


# ── helpers ───────────────────────────────────────────────────────────────────
def _center(bbox: list) -> tuple:
    x1, y1, x2, y2 = bbox
    return (int((x1 + x2) / 2), int((y1 + y2) / 2))


def _build_writer(cap: cv2.VideoCapture, output_path: str):
    """Create an mp4 VideoWriter matching the input resolution & FPS."""
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    return cv2.VideoWriter(output_path, fourcc, fps, (w, h))


# ── main loop ─────────────────────────────────────────────────────────────────
def run(args: argparse.Namespace) -> None:
    # ── initialise modules ────────────────────────────────────────────────────
    csv_logger.init_logger(args.log)

    use_tracking = not args.no_track
    if use_tracking:
        model = Tracker(
            model_path=args.model,
            conf_threshold=args.conf,
            device=args.device,
        )
    else:
        model = Detector(
            model_path=args.model,
            conf_threshold=args.conf,
            device=args.device,
        )

    traj = TrajectoryStore(max_len=30)

    # ── open video source ─────────────────────────────────────────────────────
    source = int(args.source) if args.source.isdigit() else args.source
    cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open source: {args.source}")
        sys.exit(1)

    writer = None
    if args.save_video:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        writer = _build_writer(cap, str(output_path))
        print(f"[INFO] Saving output to {output_path}")

    print("[INFO] Press 'q' to quit.")

    frame_number = 0
    prev_time = time.perf_counter()

    while True:
        ret, frame = cap.read()
        # Skip old frames
        for _ in range(2):
            cap.grab()
        if not ret:
            break

        frame_number += 1

        # ── detection / tracking ──────────────────────────────────────────────
        if use_tracking:
            objects = model.track(frame)
        else:
            # Inject a synthetic track_id = -1 so downstream code is uniform
            raw = model.detect(frame)
            objects = [{**d, "track_id": -1} for d in raw]

        # ── update trajectories ───────────────────────────────────────────────
        active_ids = set()
        for obj in objects:
            tid = obj["track_id"]
            if tid >= 0:
                cx, cy = _center(obj["bbox"])
                traj.update(tid, (cx, cy))
                active_ids.add(tid)
        traj.purge(active_ids)

        # ── draw trajectories (behind boxes) ──────────────────────────────────
        traj.draw(frame)

        # ── draw boxes + log ─────────────────────────────────────────────────
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

        # ── FPS overlay ───────────────────────────────────────────────────────
        now = time.perf_counter()
        fps = 1.0 / (now - prev_time + 1e-9)
        prev_time = now
        draw_fps(frame, fps)

        # ── display ───────────────────────────────────────────────────────────
        cv2.imshow("YOLOv8 + ByteTrack", frame)
        if writer is not None:
            writer.write(frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # ── cleanup ───────────────────────────────────────────────────────────────
    cap.release()
    if writer is not None:
        writer.release()
    cv2.destroyAllWindows()
    print(f"[INFO] Done. Log saved to {args.log}")


# ── CLI ───────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Real-Time Vehicle and Person Detection (YOLOv8 + ByteTrack)"
    )
    p.add_argument(
        "--source", default="0",
        help="Video source: camera index (0) or path to video file (default: 0)",
    )
    p.add_argument(
        "--model", default="yolov8n.pt",
        help="YOLOv8 weights (default: yolov8n.pt — auto-downloaded on first run)",
    )
    p.add_argument(
        "--conf", type=float, default=0.40,
        help="Detection confidence threshold (default: 0.40)",
    )
    p.add_argument(
        "--device", default="cpu",
        help="Inference device: 'cpu' or '0' for first GPU (default: cpu)",
    )
    p.add_argument(
        "--no-track", action="store_true",
        help="Disable ByteTrack; run pure detection only",
    )
    p.add_argument(
        "--save-video", action="store_true",
        help="Write annotated frames to --output file",
    )
    p.add_argument(
        "--output", default="output/video/output.mp4",
        help="Output video path (default: output/video/output.mp4)",
    )
    p.add_argument(
        "--log", default="output/logs/detection_log.csv",
        help="CSV log file path (default: output/logs/detection_log.csv)",
    )
    return p.parse_args()


if __name__ == "__main__":
    run(parse_args())
