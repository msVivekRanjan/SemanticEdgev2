"""
tracker.py
----------
BYTETrack integration using the official Ultralytics built-in tracker.

Ultralytics ships ByteTrack (and BoT-SORT) as first-class trackers since
v8.0. The tracker is invoked through model.track() instead of model().
This module wraps that API and returns tracked detections that are
compatible with the rest of the pipeline.

Design decisions
----------------
* We do NOT call detector.detect() separately and then feed into a
  standalone BYTETrack instance — that would require a custom BYTETrack
  Python package whose API is not stable.
* Instead, we call model.track() which internally runs ByteTrack on top
  of the YOLOv8 detections. This is the production-recommended path per
  the Ultralytics docs.
* The Tracker class wraps this call and filters to our six target classes,
  matching the Detector interface so main.py can switch between the two.
"""

from __future__ import annotations
from typing import List, Dict, Any

from ultralytics import YOLO

TARGET_CLASSES: Dict[int, str] = {
    0:  "person",
    1:  "bicycle",
    2:  "car",
    3:  "motorcycle",
    5:  "bus",
    7:  "truck",
}

TARGET_IDS = set(TARGET_CLASSES.keys())


class Tracker:
    """
    YOLOv8 + ByteTrack tracker.

    Parameters
    ----------
    model_path : str
        Weights file tag or path (e.g. 'yolov8n.pt').
    conf_threshold : float
        Minimum detection confidence.
    device : str
        PyTorch device ('cpu', '0', …).
    persist : bool
        Keep tracker state between frames (required for stable IDs).
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        conf_threshold: float = 0.40,
        device: str = "cpu",
        persist: bool = True,
    ) -> None:
        self.conf_threshold = conf_threshold
        self.device = device
        self.persist = persist
        self.model = YOLO(model_path)

    # ------------------------------------------------------------------
    def track(self, frame) -> List[Dict[str, Any]]:
        """
        Run detection + ByteTrack on one BGR frame.

        Returns
        -------
        list of dict with keys:
            track_id : int  (–1 if no ID assigned yet)
            bbox     : [x1, y1, x2, y2]
            conf     : float
            cls_id   : int
            cls_name : str
        """
        results = self.model.track(
            frame,
            conf=self.conf_threshold,
            device=self.device,
            persist=self.persist,
            tracker="bytetrack.yaml",   # use built-in ByteTrack config
            verbose=False,
        )[0]

        tracked: List[Dict[str, Any]] = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in TARGET_IDS:
                continue

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])

            # box.id is None when the tracker hasn't assigned an ID yet
            track_id = int(box.id[0]) if box.id is not None else -1

            tracked.append(
                {
                    "track_id": track_id,
                    "bbox": [x1, y1, x2, y2],
                    "conf": conf,
                    "cls_id": cls_id,
                    "cls_name": TARGET_CLASSES[cls_id],
                }
            )

        return tracked
