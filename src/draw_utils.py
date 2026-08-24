"""
draw_utils.py
-------------
Shared drawing helpers — bounding boxes, labels, confidence scores,
and track IDs.  Kept separate so main.py stays clean.
"""

from __future__ import annotations
from typing import Dict, Tuple

import cv2
import numpy as np

# Class → fixed BGR colour
CLASS_COLORS: Dict[str, Tuple[int, int, int]] = {
    "person":     (86,  168, 255),
    "bicycle":    (255, 200,  60),
    "car":        (60,  255, 160),
    "motorcycle": (255,  80, 200),
    "bus":        (80,  200, 255),
    "truck":      (255, 130,  80),
}

_DEFAULT_COLOR = (200, 200, 200)


def draw_box(
    frame: np.ndarray,
    bbox: list,
    track_id: int,
    cls_name: str,
    conf: float,
) -> None:
    """
    Draw a bounding box + label on *frame* in-place.

    Label format:  "#<track_id> <cls_name> <conf%>"
    """
    x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
    color = CLASS_COLORS.get(cls_name, _DEFAULT_COLOR)

    # Box
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2, lineType=cv2.LINE_AA)

    # Label background
    label = f"#{track_id} {cls_name} {conf * 100:.1f}%"
    (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
    ly = max(y1 - 4, th + 4)
    cv2.rectangle(frame, (x1, ly - th - 4), (x1 + tw + 4, ly + baseline), color, -1)

    # Label text (dark on coloured background)
    cv2.putText(
        frame,
        label,
        (x1 + 2, ly),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (20, 20, 20),
        1,
        lineType=cv2.LINE_AA,
    )


def draw_fps(frame: np.ndarray, fps: float) -> None:
    """Overlay FPS counter in the top-left corner."""
    cv2.putText(
        frame,
        f"FPS: {fps:.1f}",
        (10, 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 128),
        2,
        lineType=cv2.LINE_AA,
    )
