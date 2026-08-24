"""
logger.py
---------
CSV-based detection/tracking logger.

Design
------
* Single function interface: `log_entry(entry: dict)`.
* Uses pandas to append rows; the CSV header is written only once.
* Designed so it can be swapped for an SQLite backend without changing
  the callers — just replace this file with a logger_sqlite.py that
  exposes the same `init_logger()` and `log_entry()` functions.
"""

from __future__ import annotations
import os
from datetime import datetime
from typing import Optional

import pandas as pd

# Default log path (override via init_logger)
_LOG_PATH: str = "detection_log.csv"

_COLUMNS = [
    "timestamp",
    "frame_number",
    "track_id",
    "class",
    "confidence",
    "x1", "y1", "x2", "y2",
    "center_x", "center_y",
    "line_crossing_status",
]


def init_logger(log_path: str = "detection_log.csv") -> None:
    """
    Set the output path and write the CSV header if the file does not
    exist yet.

    Call this once at application start-up before any `log_entry` call.
    """
    global _LOG_PATH
    _LOG_PATH = log_path

    if not os.path.exists(_LOG_PATH):
        # Write header only
        pd.DataFrame(columns=_COLUMNS).to_csv(_LOG_PATH, index=False)


def log_entry(
    *,
    frame_number: int,
    track_id: int,
    cls_name: str,
    confidence: float,
    bbox: list,          # [x1, y1, x2, y2]
    center: tuple,       # (cx, cy)
    line_crossing_status: str = "none",
    timestamp: Optional[str] = None,
) -> None:
    """
    Append one row to the CSV log.

    Parameters
    ----------
    frame_number : int
    track_id : int
    cls_name : str
    confidence : float
    bbox : [x1, y1, x2, y2]
    center : (cx, cy)
    line_crossing_status : str  default "none"
    timestamp : str | None      ISO-8601; auto-generated if None
    """
    if timestamp is None:
        timestamp = datetime.now().isoformat()

    x1, y1, x2, y2 = bbox
    cx, cy = center

    row = pd.DataFrame(
        [
            {
                "timestamp": timestamp,
                "frame_number": frame_number,
                "track_id": track_id,
                "class": cls_name,
                "confidence": round(confidence, 4),
                "x1": round(x1, 1),
                "y1": round(y1, 1),
                "x2": round(x2, 1),
                "y2": round(y2, 1),
                "center_x": round(cx, 1),
                "center_y": round(cy, 1),
                "line_crossing_status": line_crossing_status,
            }
        ],
        columns=_COLUMNS,
    )

    row.to_csv(_LOG_PATH, mode="a", header=False, index=False)
