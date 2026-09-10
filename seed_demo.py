"""
seed_demo.py
------------
Seeds initial data for local development:
- Default superuser: admin / admin123
- Default demo user: demo / demo123
- Default demo Camera (webcam 0)
- Complete catalogue of 9 model-driven documentation pages
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
            name="Primary Sensor (Webcam)",
            defaults={
                "source_url": "0",
                "tracker_enabled": True,
                "is_active": True,
            }
        )
        if created:
            print(f"  ✓ Created camera '{cam.name}' for user '{user.username}'")

    print("[Seed] Seeding complete documentation catalogue (9 pages)...")
    docs_data = [
        # 1. Getting Started
        {
            "title": "Getting Started with SemanticEdge",
            "slug": "getting-started",
            "category": "Quick Start",
            "order": 1,
            "content_markdown": """# Getting Started with SemanticEdge

Welcome to **SemanticEdge**, the open-source Edge AI Network Video Recorder (NVR) engineered for local real-time object detection, multi-object tracking, and automated security operations.

---

## Key Capabilities

- **Zero Cloud Dependence**: Video streams are processed strictly on local hardware. Feeds, snapshots, and biometric profiles never leave your private network boundary.
- **YOLOv8 Real-Time Inference**: High-speed object detection powered by Ultralytics YOLOv8 with FP32/FP16 precision.
- **ByteTrack Tracking**: Kalman-filtered persistent track identities across occlusions and sensor noise.
- **Perimeter Monitoring Zones**: Dynamic polygon restricted areas and tripwires with instant automated intrusion alerting.
- **Telegram Security Assistant**: Interactive natural-language surveillance queries, session authentication, and automated CCTV breach notifications.
- **Biometric Face Recognition**: Real-time face matching and automated attendance audit logging.
- **Industrial Object Counting**: Line-crossing counters with conveyor rate-per-minute metrics.
- **Evidence Exporter**: Browser-playable H.264 / AVC1 clip trimming, snapshot extraction, and CSV detection log downloads.

---

## NVR Navigation Console

The SemanticEdge console provides 8 specialized operational tabs:

1. **Live Grid (`/nvr/live/`)**: Multi-camera 2x2/4-up live video grid.
2. **AI Focus (`/nvr/camera/<id>/`)**: Single-camera viewport with real-time bounding boxes, track IDs, and confidence overlays.
3. **Review Timeline (`/nvr/review/`)**: Chronological event gallery with relative timestamps and camera/class filters.
4. **Object Explore (`/nvr/explore/`)**: Category discovery strips (Persons, Cars, Trucks, Motorcycles, Bicycles, Buses).
5. **Evidence Exporter (`/nvr/export/`)**: MP4 clip trimmer with H.264 player and CSV log exports (`/nvr/export/csv/`).
6. **Face Recognition (`/nvr/face-recognition/`)**: Biometric face profile registration and live attendance logs.
7. **Object Counter (`/nvr/object-counter/`)**: Factory conveyor counting, IN/OUT totals, and rate per minute.
8. **Settings (`/nvr/settings/`)**: Camera registration, night mode thresholds, and Telegram alert verification button.

---

## Running the Services

### 1. Web & NVR Application

```bash
python manage.py runserver 127.0.0.1:8000
```

Open your browser at `http://127.0.0.1:8000/`.

### 2. Telegram Security Assistant (Optional Daemon)

```bash
python manage.py run_openclaw_bot
```

---

## Default Credentials

| Role | Username | Password |
|---|---|---|
| Administrator | `admin` | `admin123` |
| Standard User | `demo` | `demo123` |

---

## Running the Automated Test Suite

SemanticEdge includes 36 automated unit tests covering all routes, permissions, markdown rendering, and edge AI services:

```bash
python manage.py test accounts core docs nvr
```
"""
        },

        # 2. Supported Classes & Biometrics
        {
            "title": "Supported Object Classes & Biometrics",
            "slug": "supported-classes",
            "category": "Detection & Tracking",
            "order": 2,
            "content_markdown": """# Supported Object Classes & Biometrics

SemanticEdge filters standard COCO-80 object detections into **6 primary security and vehicle classes**, alongside custom biometric face reference profiles:

| Class Name | COCO ID | Color Code | Hex Value | Primary Surveillance Application |
|---|:---:|:---:|:---:|---|
| `person` | 0 | Amber | `#ffa856` | Perimeter intrusion, pedestrian tracking, line crossing |
| `bicycle` | 1 | Cyan | `#3cc8ff` | Bike lane & sidewalk monitoring |
| `car` | 2 | Lime | `#a0ff3c` | Vehicle access, parking, traffic analysis |
| `motorcycle` | 3 | Magenta | `#c850ff` | Two-wheeler traffic counting & unauthorized entry |
| `bus` | 5 | Yellow | `#ffc850` | Public transit bays & terminal monitoring |
| `truck` | 7 | Blue | `#5082ff` | Commercial loading bays & freight logistics |
| `Face Reference` | Custom | Violet | `#a855f7` | Biometric attendance & staff/student recognition |

---

## Inference & Tracking Pipeline

1. **Frame Capture**: Input frame acquired from USB webcam or network RTSP stream.
2. **YOLOv8 Inference**: Evaluated on target hardware (`cpu`, NVIDIA CUDA `0`, or Apple Silicon `mps`).
3. **Class & Confidence Filtering**: Detections with confidence >= `YOLO_CONF_THRESHOLD` (default 0.40) and class in `{0, 1, 2, 3, 5, 7}` are retained.
4. **ByteTrack Association**: Kalman filter predictions match detection boxes across frames, assigning persistent `track_id` integers.
5. **Zone Intrusion Evaluation**: Center coordinates `(cx, cy)` are tested against active polygon or tripwire geometries.
6. **Telemetry & Audit Logging**: Detections are logged to SQLite (`DetectionEvent`) and the rolling CSV audit trail.
"""
        },

        # 3. Camera Configuration & Multi-Stream Management
        {
            "title": "Camera Configuration & Multi-Stream Management",
            "slug": "camera-configuration",
            "category": "Configuration",
            "order": 3,
            "content_markdown": """# Camera Configuration & Multi-Stream Management

SemanticEdge supports local USB webcams, virtual video loopbacks (`v4l2loopback`), pre-recorded video files, and network RTSP streams.

---

## Adding a Camera

1. Navigate to **NVR > Settings** or the [Django Admin](/admin/).
2. Under **Cameras**, click **Add Camera**.
3. Configure the source parameters:
   - **Name**: Human-readable label (e.g., `Front Gate PTZ` or `Main Road Intersection`).
   - **Source URL**:
     - Local Webcam: `0`, `1`, or `2`
     - Video File: `/path/to/surveillance_sample.mp4`
     - Network RTSP: `rtsp://username:password@192.168.1.100:554/live/ch0`
   - **Tracker Enabled**: Check to activate ByteTrack multi-object tracking. Disable for detection-only mode.
   - **Night Threshold**: Grayscale mean intensity threshold (default `60.0`) below which the scene switches to Night Mode.

---

## Camera Soft-Delete Architecture

SemanticEdge employs an intelligent soft-delete reuse pattern:

- Deleting a camera from the UI toggles `is_active=False` rather than executing a hard SQL deletion.
- If a camera with the same source URL is later re-registered, the existing record is automatically reactivated (`is_active=True`).
- **Advantage**: Historical detection events, snapshots, and track IDs remain linked to the camera record without data loss or orphan keys.

---

## Multi-Camera Grid vs. AI Focus Mode

- **Multi-Camera Grid (`/nvr/live/`)**: Displays all active cameras in a responsive 2x2 or 4-up matrix with live FPS counters.
- **AI Focus View (`/nvr/camera/<id>/`)**: Dedicated single-camera viewport displaying real-time bounding boxes, track labels, confidence scores, and historical event logs for that specific sensor.
"""
        },

        # 4. Telegram Security Assistant & OpenClaw
        {
            "title": "Telegram Security Assistant & OpenClaw NLP",
            "slug": "telegram-security-assistant",
            "category": "Integrations & Alerts",
            "order": 4,
            "content_markdown": """# Telegram Security Assistant & OpenClaw NLP

SemanticEdge includes an interactive Telegram Security Assistant powered by the OpenClaw natural language processing engine. It acts as a dedicated operational interface for physical security teams.

---

## Configuration

In your `.env` file, configure the bot credentials:

```ini
TELEGRAM_BOT_TOKEN=8533970656:AAFl1aQ4G...
TELEGRAM_CHAT_ID=1448272968
```

> [!IMPORTANT]
> The `TELEGRAM_CHAT_ID` must be the Telegram User ID of the operator, NOT the bot's own ID. Telegram rejects messages where a bot attempts to send messages to itself (`HTTP 403 Forbidden`).

---

## Running the Poller Daemon

To receive and respond to incoming Telegram queries, start the dedicated single-consumer poller:

```bash
python manage.py run_openclaw_bot
```

---

## Interactive Authentication Flow

To protect sensitive surveillance footage, unauthenticated users cannot query surveillance data:

1. Send `/start` to the bot.
2. The assistant prompts: `Please enter your NVR username to authenticate:`.
3. Enter your username (e.g. `admin`).
4. Enter your password (e.g. `admin123`).
5. Upon successful validation against Django's `auth_user` table, your session is authenticated, greeted by name, and provided with the capabilities menu.
6. **Direct Command**: You can also log in directly via `/login <username> <password>`.
7. **Session Termination**: Send `/logout` to terminate your session.

---

## Operational Surveillance Queries

Once authenticated, the assistant supports comprehensive natural-language requests:

| Operational Request | Intent | Output |
|---|---|---|
| `latest intrusion` | `latest_intrusion` | Most recent breach report + snapshot photo |
| `alerts today` | `alerts_filter` | Summary count and list of today's events |
| `alerts for Front Door` | `alerts_filter` | Filtered events for the specified camera |
| `evidence for track 5` | `track_id` | Full detection metadata + snapshot for Track #5 |
| `event 104` | `event_id` | Snapshot and metadata for Event ID 104 |
| `camera status` | `camera_status` | Status, source, day/night mode for all cameras |
| `system status` | `system_status` | CPU %, RAM, disk storage, and media archive size |
| `detection statistics` | `detection_statistics` | Event counts, intrusion total, class breakdown |
| `monitoring zones` | `monitoring_zones` | List of active polygon zones and tripwires |
| `export requests` | `export_requests` | Available exported video clips and status |

---

## User Feedback Loop

Following every served operational query, the assistant prompts:

```text
Was this information helpful? (Reply YES or NO)
```

Replying `YES` or `NO` saves the feedback, timestamp, user, intent, and query text into the `TelegramFeedback` database table for auditing and continuous improvement.

---

## Professional CCTV Formatting Standard

All alerts, reports, and query responses strictly adhere to a **zero-emoji CCTV formatting standard** using clean ASCII dividers:

```text
SEMANTICEDGE INTRUSION ALERT
----------------------------------------
CAMERA      : Front Door
ZONE        : Perimeter Gate
OBJECT      : Person
TRACK ID    : #14
CONFIDENCE  : 93%
TIMESTAMP   : 2026-09-10 10:45:12
STATUS      : Restricted Area Breach
----------------------------------------
Restricted area breach detected.
```
"""
        },

        # 5. Perimeter Monitoring Zones & Intrusion Detection
        {
            "title": "Perimeter Monitoring Zones & Intrusion Detection",
            "slug": "monitoring-zones-intrusion",
            "category": "Intrusion & Security",
            "order": 5,
            "content_markdown": """# Perimeter Monitoring Zones & Intrusion Detection

SemanticEdge enables operators to draw virtual security zones and tripwires directly onto camera coordinates, transforming passive video into proactive perimeter defense.

---

## Monitoring Zone Types

SemanticEdge provides two zone geometries via the `MonitoringZone` model:

1. **Restricted Area (`polygon`)**: A closed 2D polygon defined by 3 or more vertices. Any tracked object whose center coordinate `(cx, cy)` enters the polygon triggers an intrusion alarm.
2. **Tripwire (`line`)**: A virtual boundary line defined by two endpoints. Objects crossing the vector threshold trigger a line-crossing breach.

---

## Normalized Coordinate System

All zone coordinates are stored in the database as normalized points with values between `0.0` and `1.0`:

```json
[
  [0.15, 0.20],
  [0.85, 0.20],
  [0.85, 0.75],
  [0.15, 0.75]
]
```

### Why Normalization Matters
- **Resolution Invariance**: Normalized coordinates ensure that zones drawn on a 720p browser preview correctly map to high-resolution 1080p or 4K RTSP streams.
- **Aspect Ratio Resiliency**: The streaming generator dynamically multiplies normalized coordinates by the active frame width and height (`x * W`, `y * H`).

---

## Target Class Filtering

Each monitoring zone can be constrained to specific target classes:
- Empty list `[]`: Monitors all detected object classes.
- Filtered list `["person"]`: Only triggers alarms when pedestrians breach the zone (ignoring vehicles or wildlife).
- Vehicle list `["car", "truck", "bus"]`: Enforces restricted vehicle parking zones.

---

## Intrusion Alert Pipeline

When a breach is detected:
1. `streaming.py` flags the frame and renders an **Amber/Red perimeter alert box**.
2. A single `DetectionEvent` is saved to SQLite with `line_crossing_status="Intrusion: <Zone Name>"`.
3. An evidence snapshot JPEG is saved to `media/snapshots/`.
4. `send_telegram_alert(event)` is dispatched asynchronously via a background worker thread.
"""
        },

        # 6. Face Recognition & Biometric Attendance
        {
            "title": "Face Recognition & Biometric Attendance",
            "slug": "face-recognition-attendance",
            "category": "Biometrics & Access",
            "order": 6,
            "content_markdown": """# Face Recognition & Biometric Attendance

SemanticEdge provides an edge-based biometric face recognition pipeline for enterprise access control, university classroom attendance, and automated identity verification.

---

## Enrolling Face References

1. Navigate to **NVR > Face Recognition** (`/nvr/face-recognition/`).
2. Click **Enroll New Face**.
3. Complete the employee or student profile:
   - **Full Name**: e.g., `Dr. Jane Doe`
   - **Person / Student ID**: e.g., `EMP-2026-088`
   - **Department**: e.g., `Biomedical Engineering`
   - **Reference Photo**: Upload a clear, front-facing portrait photograph.
4. The system validates and indexes the reference photo under `media/faces/references/`.

---

## Real-Time Attendance Pipeline

1. **Face Detection**: Detected bounding boxes classified as `person` are evaluated by the facial landmark extractor.
2. **Embedding Comparison**: 128-dimensional facial feature vectors are compared against all registered `FaceReference` profiles using Euclidean distance / cosine similarity.
3. **Thresholding**: Matches meeting the confidence threshold (default `0.85`) are tagged with the person's identity.
4. **Attendance Logging**: Successful matches create an immutable `AttendanceRecord` entry containing:
   - Matched `FaceReference` profile
   - Detecting `Camera` sensor
   - Confidence score (e.g., `94.2%`)
   - Status (`Present`)
   - Exact UTC/Local timestamp

---

## Viewing Attendance Logs

Review historical attendance records filtered by date, department, or camera feed directly from the **Face Recognition** tab or export records to CSV.
"""
        },

        # 7. Industrial Object Counter & Conveyor Analytics
        {
            "title": "Industrial Object Counter & Conveyor Analytics",
            "slug": "object-counter-industrial",
            "category": "Industrial Analytics",
            "order": 7,
            "content_markdown": """# Industrial Object Counter & Conveyor Analytics

SemanticEdge includes an automated object counting engine for manufacturing assembly lines, warehouse conveyor belts, and vehicle toll plazas.

---

## Line-Crossing Counting Architecture

The object counter tracks moving items across a calibrated virtual detection line:

1. **Trajectory Analysis**: Each tracked object maintains a 30-frame temporal trajectory buffer recording past center points `[(x1, y1), (x2, y2), ...]`.
2. **Vector Intersect**: When an object's trajectory vector intersects the virtual counting line, the orientation determines the direction:
   - **IN (+1)**: Movement from top-to-bottom or left-to-right across the threshold.
   - **OUT (+1)**: Movement in the reverse direction.
3. **Duplicate Suppression**: Each persistent `track_id` is registered in an internal deduplication cache so an item is counted exactly once during its crossing.

---

## Throughput & Rate-Per-Minute Metrics

The counter engine aggregates throughput metrics in real time:
- **Total Count**: `IN + OUT` units processed.
- **Net Flow**: `IN - OUT` differential.
- **Rate Per Minute**: Moving average of units processed over a rolling 60-second window.

---

## Database Telemetry (`ObjectCountRecord`)

Counting events are periodically committed to SQLite via the `ObjectCountRecord` model:
- `item_type`: Category of manufactured unit (e.g. `Pallet`, `Box`, `Bottles`).
- `in_count` / `out_count`: Directional totals.
- `rate_per_minute`: Throughput velocity.
- `created_at`: Batch timestamp.

Operators can inspect live conveyor metrics and view production graphs on `/nvr/object-counter/`.
"""
        },

        # 8. Evidence Exporter & Video Transcoding
        {
            "title": "Evidence Exporter & Video Transcoding",
            "slug": "evidence-export-transcoding",
            "category": "Evidence & Archival",
            "order": 8,
            "content_markdown": """# Evidence Exporter & Video Transcoding

The **Evidence Exporter** (`/nvr/export/`) allows security teams to package surveillance footage into courtroom-admissible, web-playable evidence bundles.

---

## Video Clip Extraction

1. Navigate to **NVR > Export** (`/nvr/export/`).
2. Select the target camera and desired time window.
3. Choose the export format:
   - **Annotated MP4**: Video clip with rendered bounding boxes, track labels, and confidence overlays.
   - **Raw Video**: Clean source footage without graphics.
4. Click **Extract Clip**.

---

## Browser-Compatible H.264 / AVC1 Transcoding

Standard OpenCV video writers frequently use `mp4v` (MPEG-4 Part 2), which fails to play natively in modern web browsers like Safari, Chrome, and Edge.

### SemanticEdge Transcoding Architecture:
1. **Primary Encoder**: The video writer targets the `avc1` codec fourcc (`cv2.VideoWriter_fourcc(*'avc1')`).
2. **FFmpeg Fallback**: If hardware codecs are unavailable, the exporter automatically invokes an FFmpeg subprocess transcode:
   ```bash
   ffmpeg -y -i input_clip.mp4 -vcodec libx264 -pix_fmt yuv420p -movflags +faststart output_clip.mp4
   ```
3. **Web-Ready FastStart**: `-movflags +faststart` shifts the MP4 atom index to the beginning of the file, allowing instant streaming in HTML5 `<video>` tags without buffering the entire file.

---

## Snapshot Archival & CSV Telemetry

- **Snapshot Storage**: Detections are saved to `media/snapshots/` as individual JPEG files indexed by date and Track ID.
- **CSV Detection Export (`/nvr/export/csv/`)**: Downloads an audit-ready CSV file containing:
  ```csv
  Event ID,Camera,Track ID,Class,Confidence,BBox Coordinates,Status,Timestamp
  104,Front Door,5,person,0.94,"[120, 80, 240, 380]",Intrusion: Gate,2026-09-10 10:45:12
  ```
"""
        },

        # 9. Lightweight Cloud Deployment (Render / PaaS)
        {
            "title": "Lightweight Cloud Deployment (Render / PaaS)",
            "slug": "lightweight-cloud-deployment",
            "category": "Deployment & DevOps",
            "order": 9,
            "content_markdown": """# Lightweight Cloud Deployment (Render / PaaS)

While edge NVR video streaming requires local camera hardware, SemanticEdge can also be deployed to cloud PaaS providers (Render, Fly.io, Heroku, AWS App Runner) for web dashboard access, documentation hosting, and SaaS demonstration.

---

## Lightweight Dependency Specification (`requirements-render.txt`)

To deploy to cloud platforms without installing massive 2GB+ PyTorch and CUDA dependencies, use `requirements-render.txt`:

```text
django>=4.2,<6.2
python-decouple>=3.8
Pillow>=10.0.0
psutil>=5.9.0
gunicorn>=23.0.0
whitenoise>=6.7.0
markdown2>=2.4.0
pygments>=2.17.0
pandas>=2.2.0
```

---

## Deploying to Render

### 1. Create a New Web Service
1. Connect your GitHub repository to [Render](https://render.com/).
2. Select **Python 3** environment.

### 2. Configure Build & Start Commands
- **Build Command**:
  ```bash
  pip install -r requirements-render.txt && python manage.py migrate && python seed_demo.py && python manage.py collectstatic --noinput
  ```
- **Start Command**:
  ```bash
  gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
  ```

### 3. Environment Variables
Add the following environment variables in the Render Dashboard:

| Key | Example Value | Description |
|---|---|---|
| `SECRET_KEY` | `your-secure-random-key` | Django secret key |
| `DEBUG` | `False` | Production security mode |
| `ALLOWED_HOSTS` | `semanticedge.onrender.com` | Allowed hostnames |
| `TELEGRAM_BOT_TOKEN` | `8533970656:AAFl1a...` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | `1448272968` | Operator chat ID |
| `YOLO_DEVICE` | `cpu` | Inference compute target |

---

## Production Security Checklist

- **WhiteNoise Static Hosting**: WhiteNoise automatically compresses and serves CSS, JavaScript, and fonts with long-term cache headers.
- **Database Backup**: Use Render Managed PostgreSQL or mount a persistent disk volume for `db.sqlite3` and `media/`.
- **SSL Termination**: Render automatically provisions free TLS/SSL certificates via Let's Encrypt.
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
            # Update existing page content and metadata
            for key, val in d.items():
                setattr(page, key, val)
            page.save()
            print(f"  ✓ Updated doc page '{page.title}'")

    print("[Seed] Complete! 9 documentation pages seeded successfully.")


if __name__ == "__main__":
    seed()
