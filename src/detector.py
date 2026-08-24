"""
detector.py
-----------
YOLOv8 detection wrapper.
Loads the model once and exposes a clean detect() API.
Only the six required COCO classes are returned.
"""

from __future__ import annotations
from typing import List, Dict, Any

from ultralytics import YOLO

# ── COCO class IDs for the six target classes ─────────────────────────────
TARGET_CLASSES: Dict[int, str] = {
    0:  "person",
    1:  "bicycle",
    2:  "car",
    3:  "motorcycle",
    5:  "bus",
    7:  "truck",
}

TARGET_IDS = set(TARGET_CLASSES.keys())


class Detector:
    """
    Thin wrapper around Ultralytics YOLOv8.

    Parameters
    ----------
    model_path : str
        Path to a .pt weights file, or a model tag such as 'yolov8n.pt'.
        The file is downloaded automatically on first use.
    conf_threshold : float
        Minimum confidence to keep a detection.
    device : str
        PyTorch device string: 'cpu', '0', 'cuda', etc.
    """

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        conf_threshold: float = 0.40,
        device: str = "cpu",
    ) -> None:
        self.conf_threshold = conf_threshold
        self.device = device
        self.model = YOLO(model_path)

    # ------------------------------------------------------------------
    def detect(self, frame) -> List[Dict[str, Any]]:
        """
        Run inference on a single BGR frame (numpy array).

        Returns
        -------
        list of dict, each with keys:
            bbox   : [x1, y1, x2, y2]  (float)
            conf   : float
            cls_id : int
            cls_name : str
        """
        results = self.model(
            frame,
            conf=self.conf_threshold,
            device=self.device,
            verbose=False,
        )[0]

        detections: List[Dict[str, Any]] = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id not in TARGET_IDS:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            detections.append(
                {
                    "bbox": [x1, y1, x2, y2],
                    "conf": conf,
                    "cls_id": cls_id,
                    "cls_name": TARGET_CLASSES[cls_id],
                }
            )

        return detections
