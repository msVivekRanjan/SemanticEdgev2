"""
trajectory.py
-------------
Maintains and draws the per-track trajectory (last N centre points).
This module is independent of detection and tracking logic.
"""

from __future__ import annotations
from collections import defaultdict, deque
from typing import Dict, Deque, Tuple

import cv2
import numpy as np

# Colour palette — one colour per track_id (cycling)
_PALETTE = [
    (255, 0,   0),    # blue
    (0,   255, 0),    # green
    (0,   0,   255),  # red
    (255, 255, 0),    # cyan
    (255, 0,   255),  # magenta
    (0,   255, 255),  # yellow
    (128, 0,   255),  # violet
    (255, 128, 0),    # orange
]


def _track_color(track_id: int) -> Tuple[int, int, int]:
    return _PALETTE[track_id % len(_PALETTE)]


class TrajectoryStore:
    """
    Stores the centre-point history for every active track.

    Parameters
    ----------
    max_len : int
        Maximum number of historical points to retain per track.
    """

    def __init__(self, max_len: int = 30) -> None:
        self.max_len = max_len
        self._history: Dict[int, Deque[Tuple[int, int]]] = defaultdict(
            lambda: deque(maxlen=self.max_len)
        )

    # ------------------------------------------------------------------
    def update(self, track_id: int, center: Tuple[int, int]) -> None:
        """Push a new centre point for a given track."""
        self._history[track_id].append(center)

    # ------------------------------------------------------------------
    def draw(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw all stored trajectories onto *frame* (in-place).

        Returns the annotated frame.
        """
        for track_id, points in self._history.items():
            if len(points) < 2:
                continue
            pts = np.array(list(points), dtype=np.int32).reshape(-1, 1, 2)
            color = _track_color(track_id)
            cv2.polylines(
                frame,
                [pts],
                isClosed=False,
                color=color,
                thickness=2,
                lineType=cv2.LINE_AA,
            )
        return frame

    # ------------------------------------------------------------------
    def purge(self, active_ids: set) -> None:
        """
        Remove history for tracks that are no longer active.
        Call this once per frame with the set of current track IDs.
        """
        stale = [tid for tid in self._history if tid not in active_ids]
        for tid in stale:
            del self._history[tid]
