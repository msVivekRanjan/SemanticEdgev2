"""
seed_demo.py
------------
Seeds initial data for local development:
- Default superuser: admin / admin123
- Default demo user: demo / demo123
- Default demo Camera (webcam 0)
- Sample documentation pages
"""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Ensure semanticedge and repo root are in python path
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import django
django.setup()

from django.contrib.auth.models import User
from docs.models import DocPage
from nvr.models import Camera


def seed():
    print("[Seed] Creating users...")
    admin_user, created = User.objects.get_or_create(
        username="admin",
        defaults={"email": "admin@semanticedge.internal", "is_staff": True, "is_superuser": True}
    )
    if created:
        admin_user.set_password("admin123")
        admin_user.save()
        print("  ✓ Created superuser: 'admin' (password: 'admin123')")
    else:
        print("  ℹ Superuser 'admin' already exists")

    demo_user, created = User.objects.get_or_create(
        username="demo",
        defaults={"email": "demo@semanticedge.internal"}
    )
    if created:
        demo_user.set_password("demo123")
        demo_user.save()
        print("  ✓ Created user: 'demo' (password: 'demo123')")
    else:
        print("  ℹ User 'demo' already exists")

    print("[Seed] Creating default cameras...")
    for user in [admin_user, demo_user]:
        cam, created = Camera.objects.get_or_create(
            owner=user,
            name=f"Primary Sensor (Webcam)",
            defaults={
                "source_url": "0",
                "tracker_enabled": True,
                "is_active": True,
            }
        )
        if created:
            print(f"  ✓ Created camera '{cam.name}' for user '{user.username}'")

    print("[Seed] Creating documentation pages...")
    docs_data = [
        {
            "title": "Getting Started with SemanticEdge",
            "slug": "getting-started",
            "category": "Quick Start",
            "order": 1,
            "content_markdown": """# Getting Started with SemanticEdge

Welcome to **SemanticEdge**, the open-source NVR built for real-time edge AI object detection and multi-object tracking.

---

## Key Capabilities

- **Zero Cloud Dependence**: Video frames are processed strictly on local compute hardware. Feeds never leave your network boundary.
- **YOLOv8 Real-Time Inference**: Powered by Ultralytics YOLOv8 with high-speed FP32/FP16 models.
- **ByteTrack Tracking**: Stable persistent tracking identities across occlusions and motion.
- **Trajectory Analysis**: Active path tracking (30-frame temporal buffer) rendered behind bounding boxes.
- **Audit-Ready Logging**: Structured CSV event streaming with frame numbers, bounding boxes, confidence, and timestamps.

---

## Running the Web Application

To start the local streaming server:

```bash
cd semanticedge
python manage.py runserver 127.0.0.1:8000
```

Open your browser at `http://127.0.0.1:8000/`.

---

## Default Credentials

For quick evaluation, seed credentials are created:

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `admin123` |
| Standard User | `demo` | `demo123` |
"""
        },
        {
            "title": "Supported Object Classes",
            "slug": "supported-classes",
            "category": "Detection & Tracking",
            "order": 2,
            "content_markdown": """# Supported Object Classes

SemanticEdge filters standard COCO-80 object detections into **6 primary security and vehicle classes**:

| Class Name | COCO ID | Color Code | Security Priority |
|---|---|---|---|
| `person` | 0 | Amber / `#ffa856` | High |
| `bicycle` | 1 | Cyan / `#3cc8ff` | Medium |
| `car` | 2 | Lime / `#a0ff3c` | Normal |
| `motorcycle` | 3 | Magenta / `#c850ff` | Medium |
| `bus` | 5 | Yellow / `#ffc850` | Normal |
| `truck` | 7 | Blue / `#5082ff` | Normal |

---

## Model Pipeline

1. **Input Frame**: 640x640 letterboxed frame from webcam or RTSP feed.
2. **Inference**: YOLOv8 neural network evaluated on target hardware (`cpu` or CUDA `0`).
3. **Filter**: Detections with confidence >= `YOLO_CONF_THRESHOLD` (default 0.40) and class in `{0, 1, 2, 3, 5, 7}` are retained.
4. **ByteTrack**: Kalman filter and bipartite matching assign persistent `track_id` integers.
"""
        },
        {
            "title": "Camera Configuration & RTSP",
            "slug": "camera-configuration",
            "category": "Configuration",
            "order": 3,
            "content_markdown": """# Camera Configuration

SemanticEdge supports local USB webcams, virtual video loopbacks (`v4l2loopback`), and network RTSP streams.

---

## Adding a Camera via Admin

1. Log in to the [Django Admin](/admin/).
2. Navigate to **NVR > Cameras > Add Camera**.
3. Set the fields:
   - **Name**: e.g., `Front Gate PTZ`
   - **Source URL**: 
     - Webcam index: `0` or `1`
     - Video file: `/path/to/security_footage.mp4`
     - RTSP Stream: `rtsp://user:password@192.168.1.100:554/h264Preview_01_main`
   - **Tracker Enabled**: Check to activate ByteTrack tracking.

> [!WARNING]
> RTSP URLs with embedded authentication credentials are saved in the local database. For production deployments with multiple untrusted admins, use environment variable indirection.
"""
        }
    ]

    for d in docs_data:
        page, created = DocPage.objects.get_or_create(
            slug=d["slug"],
            defaults=d
        )
        if created:
            print(f"  ✓ Created doc page '{page.title}'")
        else:
            print(f"  ℹ Doc page '{page.title}' already exists")

    print("[Seed] Complete!")


if __name__ == "__main__":
    seed()
