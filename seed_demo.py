"""
seed_demo.py
------------
Seeds initial data for development and Render Showcase Mode.

Always seeded (both modes):
  - Default superuser: admin / admin123
  - Default demo user: demo / demo123
  - Complete catalogue of 11 model-driven documentation pages

Only seeded when SHOWCASE_MODE=false (full local/NVR mode):
  - Default demo Camera (webcam 0) for each user
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

from django.conf import settings
from django.contrib.auth.models import User
from docs.models import DocPage

# Determine deployment mode AFTER django.setup() so settings are fully loaded.
_SHOWCASE_MODE = getattr(settings, "SHOWCASE_MODE", False)

# Conditionally import Camera to avoid pulling in Edge-AI deps in Showcase Mode.
if not _SHOWCASE_MODE:
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

    if _SHOWCASE_MODE:
        print("[Seed] Skipping camera seeding (SHOWCASE_MODE=true — NVR not loaded)")
    else:
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

    print("[Seed] Seeding complete documentation catalogue (11 pages)...")
    docs_data = [
        {
            "title": 'Getting Started with SemanticEdge',
            "slug": 'getting-started',
            "category": 'System & Architecture',
            "order": 1,
            "content_markdown": """# Getting Started with SemanticEdge

Welcome to **SemanticEdge** — an enterprise-grade AI Network Video Recorder (NVR) engineered for local, privacy-first edge intelligence. SemanticEdge transforms standard camera streams into an intelligent, queryable security event stream using real-time YOLOv8 neural network inference, ByteTrack multi-object tracking, custom restricted intrusion zones, and an integrated in-browser Security Assistant.

---

## Key Capabilities at a Glance

- **100% Local Inference**: Zero raw video feeds or detection frames ever leave your private network perimeter.
- **Real-Time Multi-Object Tracking**: Persistent identity tracking for persons and vehicles with 30-point temporal trajectory paths.
- **Perimeter Intrusion Detection**: Configurable polygon restricted zones and virtual tripwires with immediate in-browser alert toasts.
- **Investigative Workspace**: Dual-workspace workflow combining fast multi-parameter discovery (**Review**) with a conversational security investigation assistant (**Explore**).
- **Remote 5G Ingestion**: Direct, secure ingestion of RTSP streams across cellular/5G networks using Tailscale WireGuard subnet routing.

---

## System Requirements

| Component | Minimum Specification | Recommended Production Target |
|---|---|---|
| **Operating System** | macOS 12+, Ubuntu 20.04+, Debian 11+ | Ubuntu 22.04 LTS or macOS (Apple Silicon) |
| **Python** | Python 3.10 to 3.12 | Python 3.11 |
| **Processor** | 4-Core x86_64 or ARM64 | Intel Core i7/i9, AMD Ryzen 7, or Apple M1/M2/M3/M4 |
| **Memory (RAM)** | 8 GB | 16 GB or higher |
| **Acceleration** | CPU (AVX2 / OpenVINO) | NVIDIA GPU (CUDA 11.8+) or Apple Silicon (MPS) |
| **Video Tools** | FFmpeg 4.4+ | FFmpeg 6.0+ with H.264 hardware encoders |

---

## Step-by-Step Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/semanticedge.git
cd semanticedge
```

### 2. Create and Activate a Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```
*(On Windows: `.venv\\Scripts\\activate`)*

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the example configuration to create your local `.env`:
```bash
cp .env.example .env
```

Review and adjust settings in `.env`:
```ini
# Django Application Secret
SECRET_KEY=your-secure-random-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Edge AI Model & Hardware Target
YOLO_MODEL_PATH=yolov8n.pt
YOLO_CONF_THRESHOLD=0.40
YOLO_DEVICE=cpu         # Options: 'cpu', '0' (NVIDIA GPU), 'mps' (Apple Silicon)
```

### 5. Initialize the Database & Seed Demo Data
Run standard Django migrations to create the database schema:
```bash
python manage.py migrate
```

Seed the database with initial users, default camera configuration, and documentation pages:
```bash
python seed_demo.py
```

### 6. Launch the Development Server
```bash
python manage.py runserver 127.0.0.1:8000
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your web browser.

---

## Default Access Credentials

The database seeder provisions two default user accounts:

| Username | Password | Role | Permissions |
|---|---|---|---|
| **`admin`** | `admin123` | Administrator | Full access to all cameras, configuration, zone drawing, and diagnostics |
| **`demo`** | `demo123` | Standard Operator | Access to assigned cameras, Review, Explore assistant, and Export |

---

## Post-Install Verification Checklist

1. **Dashboard & Telemetry**: Check the bottom status bar for live CPU %, RAM %, and Inference Engine status (`CPU`, `CUDA`, or `Apple MPS`).
2. **Camera Streaming**: In the **Live** view, verify that the local webcam or configured RTSP camera streams smoothly.
3. **Detection Verification**: Wave a person or object in front of the lens; verify bounding box overlay and trajectory trail display.
4. **Intrusion Alerts**: In the Tracker view, configure a test polygon zone and verify detection events in the **Review** tab.
5. **Explore Assistant**: Navigate to the **Explore** tab and type `latest intrusion` or `system status` to test the internal Security Assistant.
"""
        },
        {
            "title": 'System Architecture & Data Flow',
            "slug": 'system-architecture',
            "category": 'System & Architecture',
            "order": 2,
            "content_markdown": """# System Architecture & Data Flow

SemanticEdge is engineered from the ground up as a **local-first edge intelligence system**. Traditional cloud-based surveillance pipelines stream massive amounts of raw video bandwidth to third-party datacenters, creating severe privacy vulnerabilities, high latency, and continuous recurring cloud costs.

In contrast, SemanticEdge performs all high-bandwidth video processing, neural network inference, and multi-object tracking **strictly on local edge hardware**. Raw video streams never leave your trusted perimeter.

---

## High-Level Architecture Diagram

```text
                                +-----------------------------------+
                                |          Video Sources            |
                                |   (USB Webcam / RTSP IP Camera)  |
                                +------------------+----------------+
                                                   |
                                                   v
+----------------------------------------------------------------------------------+
|  Edge AI Inference & Tracking Pipeline  (nvr/streaming.py + src/)                |
|                                                                                  |
|  +---------------------+    +---------------------+    +--------------------+    |
|  |  YOLOv8 Inference   |    |  ByteTrack Tracking  |    |  Trajectory Store  |    |
|  |  (FP32 / FP16)      +--->|  Kalman + Hungarian  +--->|  30-pt Path Buffer |    |
|  |  Class Filter       |    |  Persistent Track ID |    |                    |    |
|  +---------------------+    +---------------------+    +----------+---------+    |
|                                                                    |             |
|                        MonitoringZone Intersection Check           |             |
|                                   --> Intrusion Detected?          |             |
|                                              |                     |             |
|                                       Yes -->+                     |             |
|                                              v                                   |
|                                 DetectionEvent persisted                         |
|                          (class, track_id, camera, snapshot,                     |
|                           bbox, line_crossing_status)                            |
+----------------------------------------------------------------------------------+
                                                   |
                                                   v
+----------------------------------------------------------------------------------+
|  Django Application Core  (nvr/, accounts/, docs/, core/)                        |
|                                                                                  |
|  +-----------------+    +------------------+    +-----------------------------+  |
|  |  Live View      |    |  Review Tab      |    |  Explore Tab                |  |
|  |  (MJPEG Stream  |    |  (Object Search  |    |  (Internal Security         |  |
|  |  + Zone Config) |    |  & Discovery)    |    |   Assistant Workspace)      |  |
|  +-----------------+    +--------+---------+    +--------------+--------------+  |
|                                  |                             |                 |
|                     Deep-link: event_id / track_id             |                 |
|                                  +--------------->-------------+                 |
|                                                                                  |
|  +----------------------------------------------------------------------------+  |
|  |  Internal Security Assistant Service  (nvr/assistant/)                     |  |
|  |                                                                             |  |
|  |  AssistantService (service.py)                                              |  |
|  |    +-- AssistantNLPEngine (nlp.py)  -- intent parsing                      |  |
|  |    +-- NVRTools (tools.py)          -- controlled, typed data access        |  |
|  |    +-- BaseLLMProvider (llm.py)     -- RuleBasedNVRProvider (default)       |  |
|  |                                                                             |  |
|  |  Models: AlertConversation, ChatMessage                                     |  |
|  +----------------------------------------------------------------------------+  |
+----------------------------------------------------------------------------------+
                                                   |
                            +----------------------+----------------------+
                            v                      v                      v
              +---------------------+  +--------------------+  +--------------------+
              |  Client Browser     |  |  SQLite /          |  |  Media Storage     |
              |  (Vanilla HTML5/JS) |  |  PostgreSQL        |  |  (snapshots,       |
              +---------------------+  +--------------------+  |   video clips)     |
                                                               +--------------------+
```

---

## Architectural Subsystems

### 1. Ingestion & Preprocessing Layer (`nvr/streaming.py`)
- Ingests video frames from local device drivers (`/dev/video*`, AVFoundation) or remote RTSP endpoints over TCP.
- Decouples acquisition into dedicated camera worker threads, maintaining a clean frame queue and dropping stale frames to prevent buffer bloat.
- Calculates real-time feed FPS and computes grayscale pixel luminance to dynamically determine day vs. night mode.

### 2. Edge AI & Multi-Object Tracking Pipeline (`src/`)
- **Detector (`src/detector.py`)**: Runs Ultralytics YOLOv8 inference, filtering output to 6 target surveillance classes (`person`, `bicycle`, `car`, `motorcycle`, `bus`, `truck`).
- **Tracker (`src/tracker.py`)**: Uses the ByteTrack algorithm to assign persistent integer Track IDs across frame boundaries via Kalman filter state prediction and Hungarian bipartite matching.
- **Trajectory Buffer (`src/trajectory.py`)**: Stores up to 30 past centroid positions per active track to calculate directional velocity and render smooth trajectory trails.

### 3. Spatial Zone & Intrusion Engine (`nvr/models.py`)
- Evaluates object centroids against polygon restricted zones and virtual tripwires.
- Performs coordinate normalization to ensure zones scale accurately across different resolutions.
- Employs non-blocking event logging: when a breach occurs, a `DetectionEvent` is saved with evidence snapshot and line-crossing status without halting stream playback.

### 4. Dual Investigative Workspaces
- **Review (`/nvr/review/`)**: Visual object discovery workspace with tokenized multi-parameter search, category strips, compact filtered grid, and two-column evidence detail modals.
- **Explore (`/nvr/explore/`)**: Conversational investigation interface. Operators converse with the internal Security Assistant to query intrusions, review track timelines, and examine audit logs.

### 5. Decoupled Assistant Layer (`nvr/assistant/`)
- Encapsulates investigative logic in an independent service.
- **`NVRTools`**: A strictly typed data-access interface that retrieves telemetry, camera status, track history, and related events without allowing arbitrary SQL injection.
- **`RuleBasedNVRProvider`**: A zero-dependency, deterministic local NLP engine that requires no external API keys or third-party cloud services.
"""
        },
        {
            "title": 'Camera & RTSP Stream Configuration',
            "slug": 'camera-rtsp-configuration',
            "category": 'Video & Networking',
            "order": 3,
            "content_markdown": """# Camera & RTSP Stream Configuration

SemanticEdge provides flexible multi-source camera management, accommodating both local direct-attached USB/MIPI sensors and networked IP cameras streaming standard RTSP feeds.

---

## Camera Data Model Schema

Each camera connected to SemanticEdge is represented by the `Camera` model in `nvr/models.py`:

```python
class Camera(models.Model):
    name = models.CharField(max_length=120)
    source_url = models.CharField(max_length=512)
    tracker_enabled = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    night_threshold = models.FloatField(default=60.0)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
```

---

## Supported Source URL Formats

### 1. Local USB / V4L2 Webcams
For directly attached cameras, specify the numeric device index:
- `"0"`: Primary default webcam (`/dev/video0` on Linux, AVFoundation 0 on macOS).
- `"1"`: Secondary external USB camera.

### 2. Network IP Cameras (RTSP)
For networked surveillance cameras, supply the complete RTSP URL:
```text
rtsp://[username]:[password]@[ip-address]:[port]/[stream-path]
```

**Common Manufacturer URI Formats:**
- **Sparsh CCTV**: `rtsp://admin:admin123@192.168.128.10:554/stream1`
- **Hikvision**: `rtsp://admin:password@192.168.1.64:554/Streaming/Channels/101`
- **Dahua**: `rtsp://admin:password@192.168.1.108:554/cam/realmonitor?channel=1&subtype=0`
- **Axis**: `rtsp://root:pass@192.168.1.50/axis-media/media.amp?videocodec=h264`

### 3. Local Video Files (Testing & Benchmarks)
For repeatable test runs or offline evaluation, pass the relative or absolute path to an MP4 video:
```text
media/test_footage/perimeter_walk.mp4
```

---

## Camera Lifecycle: Soft-Delete Semantics

In enterprise security environments, accidental or malicious deletion of camera hardware must never purge historic forensic evidence. SemanticEdge uses **soft-delete semantics**:

- When a camera is removed via the web console, `is_active` is set to `False`.
- The streaming pipeline terminates gracefully, freeing memory and GPU threads.
- All historical `DetectionEvent` records, snapshot JPEGs, and track IDs remain intact.
- Re-adding a camera with the same parameters reactivates the record and restores continuity.

---

## Dynamic Night Mode Detection

Each `Camera` record maintains a configurable `night_threshold` (default: `60.0`):

```python
# Streaming pipeline luminance check
gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
mean_intensity = float(np.mean(gray))
is_night_mode = mean_intensity < camera.night_threshold
```

When mean luminance drops below this threshold:
1. Stream overlays automatically render high-contrast labels.
2. The telemetry bar flags the camera as operating in **Night Mode**.
3. Operators can tune this sensitivity per camera in `/nvr/settings/` or via API:
   ```bash
   curl -X POST http://127.0.0.1:8000/nvr/api/camera/1/night-threshold/ \
        -H "Content-Type: application/json" \
        -d '{"night_threshold": 45.0}'
   ```

---

## Multi-Stream Threading Architecture

SemanticEdge isolates each active camera stream into an independent worker thread inside `nvr/streaming.py`:
- **Thread Safety**: Frame acquisition is decoupled from Django's HTTP request handler.
- **Fault Tolerance**: Network disconnects, RTSP socket drops, or packet loss on Camera 1 never block or degrade Camera 2.
- **Auto-Reconnect**: The capture loop attempts exponential-backoff reconnects if an RTSP socket breaks.
"""
        },
        {
            "title": '5G + Tailscale Remote Streaming',
            "slug": '5g-tailscale-remote-streaming',
            "category": 'Video & Networking',
            "order": 4,
            "content_markdown": """# 5G + Tailscale Remote Streaming

In real-world security deployments, surveillance cameras are frequently deployed in remote facilities, construction zones, or isolated private network segments such as a private 5G network. 

SemanticEdge includes a field-tested, production architecture to ingest raw RTSP camera streams across the Internet without port forwarding, without public static IP addresses, and without exposing cameras to the public web.

---

## Real-World Production Topology

This exact networking topology is actively deployed in the SemanticEdge project to ingest a Sparsh IP CCTV camera situated inside a university 5G Use Case Lab (Signaltron private 5G) from a remote MacBook processing station:

```text
+--------------------------------------------------------+
| 5G Use Case Lab (Private Network: 192.168.128.0/24)    |
|                                                        |
|  Sparsh IP CCTV (192.168.128.10)                       |
|        |                                               |
|        | RTSP over TCP (Port 554)                      |
|        v                                               |
|  ue1 Linux Gateway (192.168.128.127)                   |
|  - IP Forwarding: net.ipv4.ip_forward = 1              |
|  - Tailscale Subnet Router: 192.168.128.0/24          |
+---------------------------+----------------------------+
                            |
                     Encrypted Mesh
                   (WireGuard Tunnel)
                            |
                            v
+--------------------------------------------------------+
| Remote Processing Station (e.g. New Delhi)             |
|                                                        |
|  SemanticEdge Machine (100.118.232.36)                 |
|  - Tailscale Client (--accept-routes)                 |
|  - Direct RTSP Ingestion:                              |
|    rtsp://admin:admin123@192.168.128.10:554/stream1   |
|  - YOLOv8 Inference & ByteTrack Tracking               |
+--------------------------------------------------------+
```

---

## Step-by-Step Setup Guide

### 1. Configure the Gateway Machine (`ue1`)
The gateway machine is a Linux system with access to both the camera's local network (`192.168.128.0/24`) and the Internet.

#### A. Enable IPv4 Kernel Forwarding
```bash
# Enable immediately in runtime
sudo sysctl -w net.ipv4.ip_forward=1
sudo sysctl -w net.ipv6.conf.all.forwarding=1

# Make permanent across reboots
echo "net.ipv4.ip_forward = 1" | sudo tee /etc/sysctl.d/99-tailscale.conf
echo "net.ipv6.conf.all.forwarding = 1" | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

#### B. Advertise the Subnet Through Tailscale
```bash
sudo tailscale up --advertise-routes=192.168.128.0/24 --accept-routes
```

#### C. Approve the Subnet Route
Navigate to your **Tailscale Admin Console** -> **Machines** -> click `ue1` -> **Edit route settings** -> Enable `192.168.128.0/24`.

---

### 2. Configure the Remote Processing Station
On the remote machine running SemanticEdge:

```bash
# Start Tailscale with route acceptance enabled
sudo tailscale up --accept-routes
```

Verify reachability to the remote camera:
```bash
# 1. Test ICMP Ping
ping -c 3 192.168.128.10

# 2. Test RTSP Socket
nc -zvw3 192.168.128.10 554
# Expected output: Connection to 192.168.128.10 port 554 [tcp/rtsp] succeeded!
```

---

## Why RTSP-over-TCP is Mandatory

Over cellular or 5G connections, standard UDP transport for RTSP causes severe frame tearing, dropped macroblocks, and desynchronization due to packet fragmentation.

SemanticEdge forces **RTSP-over-TCP**:
```python
# VideoCapture configuration in nvr/streaming.py
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"
cap = cv2.VideoCapture(source_url, cv2.CAP_FFMPEG)
```

Using TCP encapsulates RTP video packets inside reliable, ordered TCP segments, ensuring zero packet loss and clean decoding even across multi-hop 5G backhauls.

---

## Advantages Over Traditional Solutions

| Feature | Port Forwarding / Dynamic DNS | Reverse SSH Tunnel | 5G + Tailscale Subnet Router |
|---|---|---|---|
| **Public IP Requirement** | Requires static public IP | Needs public VPS relay | **Zero public IP needed** |
| **NAT Traversal** | Fails behind CGNAT | Manual port mapping | **Automated WireGuard hole-punching** |
| **Security Risk** | High (open port to the internet) | Medium (SSH port exposed) | **High (Zero exposed open ports)** |
| **Throughput & Latency** | Low overhead | High SSH encryption CPU load | **Kernel WireGuard wire-speed** |
| **Multi-Camera Scalability**| Complex routing per camera | Fragile per-stream tunnels | **Entire subnet routed seamlessly** |
"""
        },
        {
            "title": 'Edge AI: YOLO Detection & ByteTrack Tracking',
            "slug": 'edge-ai-yolo-bytetrack',
            "category": 'Edge AI & Intelligence',
            "order": 5,
            "content_markdown": """# Edge AI: YOLO Detection & ByteTrack Tracking

SemanticEdge combines high-speed single-stage object detection (**Ultralytics YOLOv8**) with state-of-the-art multi-object tracking (**ByteTrack**) to convert unformatted video streams into structured, queryable spatiotemporal object tracks.

---

## Object Detection: Ultralytics YOLOv8

YOLOv8 provides anchor-free object detection with optimized convolutional backbones and decoupled heads for classification and bounding box regression.

### Target Surveillance Classes
While standard models train on the 80 COCO categories, SemanticEdge filters inference output to **6 primary security and vehicle classes**:

| Class Name | Class ID | UI Color | Hex Code | Primary Surveillance Application |
|---|:---:|:---:|:---:|---|
| **`person`** | `0` | Amber | `#ffa856` | Perimeter breach, loitering, unauthorized entry |
| **`bicycle`** | `1` | Cyan | `#3cc8ff` | Walkway monitoring, delivery tracking |
| **`car`** | `2` | Lime | `#a0ff3c` | Vehicle access, parking, traffic analysis |
| **`motorcycle`** | `3` | Magenta | `#c850ff` | Two-wheeler gate passage, speed violations |
| **`bus`** | `5` | Yellow | `#ffc850` | Transit bay occupancy, terminal security |
| **`truck`** | `7` | Blue | `#5082ff` | Commercial loading dock and logistics tracking |

---

## Multi-Object Tracking: ByteTrack

Detecting an object in single isolated frames is insufficient for surveillance. Security operators need to know **where an object came from, where it is heading, and how long it has been in the area**.

### How ByteTrack Works
Standard tracking algorithms discard low-confidence detections, leading to broken tracks when objects pass behind poles, walk through shadows, or experience partial occlusion. 

**ByteTrack solves this using a two-stage association pipeline:**
1. **High-Confidence Matching**: First associates high-confidence detections ($conf >= 0.5$) with existing active tracks using Kalman filter state prediction and Hungarian bipartite matching.
2. **Low-Confidence Recovery**: Second, instead of throwing away low-confidence boxes ($0.1 <= conf < 0.5$), it matches them against unconfirmed or temporarily lost tracks. This recovers objects obscured by obstacles without creating duplicate track IDs.

```text
Video Frame
     │
     ▼
YOLOv8 Detection Head  ──► High-Score Bounding Boxes ──► Stage 1 Association (Hungarian + Kalman)
     │                                                           │
     ▼                                                           ▼
Low-Score Bounding Boxes ──────────────────────────────► Stage 2 Association (Recovery Matching)
                                                                 │
                                                                 ▼
                                                      Persistent Track ID Assigned
```

---

## Temporal Trajectory Store (`src/trajectory.py`)

SemanticEdge maintains a rolling circular buffer of the past **30 spatial centroid coordinates** for each active track ID:

```python
class TrajectoryStore:
    def __init__(self, max_length: int = 30):
        self._tracks: dict[int, deque] = {}
        self.max_length = max_length

    def update(self, track_id: int, centroid: tuple[int, int]):
        if track_id not in self._tracks:
            self._tracks[track_id] = deque(maxlen=self.max_length)
        self._tracks[track_id].append(centroid)
```

### Practical Benefits:
- **Vector Trails**: Visual trajectory trails rendered onto live video feeds illustrate the recent movement path.
- **Directional Analysis**: Differentiates whether an object is entering or exiting a sensitive perimeter.
- **Tripwire Crossing Calculation**: Verifies that a trajectory line segment mathematically intersects a virtual boundary line.

---

## Hardware Acceleration Targets

Configure the compute backend in `.env` via `YOLO_DEVICE`:

```ini
# Options: 'cpu', '0' (CUDA), 'mps' (Apple Silicon)
YOLO_DEVICE=cpu
```

### 1. CPU (Default)
Optimized for standard x86_64 (AVX2/AVX-512) and ARM64 processors. Excellent for 1 to 2 concurrent 1080p feeds on standard edge mini-PCs.

### 2. NVIDIA CUDA GPU (`YOLO_DEVICE=0`)
Utilizes Tensor Cores and FP16 half-precision inference. Ideal for enterprise deployments running 4 to 16 concurrent high-FPS video streams.

### 3. Apple Silicon (`YOLO_DEVICE=mps`)
Directly leverages Apple's Metal Performance Shaders (MPS) unified memory architecture across M1, M2, M3, and M4 processors, providing high frame rates with ultra-low thermal dissipation.
"""
        },
        {
            "title": 'Restricted Area & Intrusion Monitoring',
            "slug": 'restricted-area-intrusion-monitoring',
            "category": 'Edge AI & Intelligence',
            "order": 6,
            "content_markdown": """# Restricted Area & Intrusion Monitoring

Perimeter security requires immediate, automated breach detection. SemanticEdge enables security teams to draw custom virtual fences, restricted zones, and tripwires directly over live camera views.

---

## Monitoring Zone Data Model

Monitoring zones are stored in `nvr/models.py`:

```python
class MonitoringZone(models.Model):
    ZONE_TYPE_CHOICES = [
        ("polygon", "Polygon Zone"),
        ("line", "Line Tripwire"),
    ]
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE, related_name="zones")
    name = models.CharField(max_length=120)
    zone_type = models.CharField(max_length=20, choices=ZONE_TYPE_CHOICES, default="polygon")
    coordinates = models.JSONField(help_text="Normalized [[x, y], ...] coordinates (0.0 to 1.0)")
    is_active = models.BooleanField(default=True)
    target_classes = models.JSONField(default=list, help_text="List of target classes, e.g. ['person']")
```

---

## Normalized Coordinate System

Cameras frequently change output resolutions (e.g. streaming 720p to save bandwidth, then switching to 1080p or 4K for recording). Absolute pixel coordinates would break whenever the resolution shifts.

SemanticEdge solves this using **proportional normalized coordinates ($0.0 <= x, y <= 1.0$)**:
```json
[
  [0.15, 0.20],
  [0.85, 0.20],
  [0.85, 0.80],
  [0.15, 0.80]
]
```

At runtime, the streaming pipeline scales normalized coordinates to the current frame width and height:
```python
pts = np.array([
    [int(x * frame_width), int(y * frame_height)]
    for x, y in zone.coordinates
], np.int32)
```

---

## Spatial Geometry & Intrusion Algorithms

### 1. Polygon Restricted Zones
For polygonal areas (e.g., restricted warehouse zones, secure perimeter courtyards), SemanticEdge tests the centroid of each detected object against the zone polygon using the **Ray-Casting Algorithm** (`cv2.pointPolygonTest`):

```python
dist = cv2.pointPolygonTest(polygon_pts, (center_x, center_y), measureDist=False)
is_inside = dist >= 0
```

### 2. Line Tripwires
For perimeter fences, doorways, or driveway boundaries, SemanticEdge checks whether the movement vector formed by the object's previous centroid and current centroid intersects the tripwire line segment using 2D orientation determinants.

---

## Non-Blocking Event Lifecycle

Surveillance streaming must never stall because of database operations or disk I/O. The intrusion detection pipeline is completely asynchronous and decoupled:

```text
[Object Enters Zone]
        │
        ▼
[Spatial Intersection True]
        │
        ├──► Draw Highlighted Red Bounding Box on Video Stream
        │
        └──► Spawn Non-Blocking Async Task:
                  │
                  ├── 1. Crop and save snapshot JPEG to media/snapshots/
                  ├── 2. Persist DetectionEvent record (with line_crossing_status)
                  └── 3. Dispatch alert payload to /nvr/api/alerts/latest/
```

### In-Browser Alert Delivery
Operators viewing any screen in the NVR receive real-time toast alerts delivered via lightweight background polling to `/nvr/api/alerts/latest/`. Each toast displays the camera name, breached zone, timestamp, and a direct link to review the captured evidence.
"""
        },
        {
            "title": 'AI-Generated Event Descriptions',
            "slug": 'ai-generated-event-descriptions',
            "category": 'Edge AI & Intelligence',
            "order": 7,
            "content_markdown": """# AI-Generated Event Descriptions

Traditional NVR systems log cryptic, isolated data rows (e.g., `Class: 0, Box: [120, 45, 200, 310]`). To understand what occurred, an operator must manually inspect hours of recorded video clips.

SemanticEdge elevates surveillance logs into **natural-language semantic narratives** stored in `DetectionEvent.description`.

---

## Purpose & Advantages

- **Instant Human Readability**: Security personnel can scan a chronological list of plain-English sentences rather than decoding bounding box coordinates.
- **Natural Language Search**: Operators can search for *"person near east gate"* or *"delivery vehicle"* and retrieve matched events instantly.
- **Context for the Security Assistant**: Provides rich contextual information to the internal Security Assistant in the **Explore** tab.

---

## How Descriptions are Stored

In `nvr/models.py`, every detection event maintains an indexed text description:

```python
class DetectionEvent(models.Model):
    camera = models.ForeignKey(Camera, on_delete=models.CASCADE)
    track_id = models.IntegerField()
    class_name = models.CharField(max_length=64)
    confidence = models.FloatField()
    line_crossing_status = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    snapshot_path = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

When an event is captured, SemanticEdge automatically formats an initial descriptive narrative:
```text
Person #14 breached restricted zone 'Perimeter East' at 14:32:05
```

When vision-language models (such as Qwen-VL or local multimodal captioners) are integrated, detailed visual descriptions are generated:
```text
Person wearing dark hooded jacket and blue jeans walking rapidly along the perimeter fence carrying a backpack.
```

---

## Interactive Operator Editing

Forensic analysts often need to append verified investigation notes, suspect identifications, or license plate numbers to detection records.

### Editing via the Review Modal
1. In the **Review** tab, click any detection card to open the **Detection Evidence & Details** modal.
2. In the right-hand metadata column, navigate to the **AI Description & Notes** field.
3. Edit the text and click **Save Description**.

### Programmatic REST API Endpoint
You can also update descriptions programmatically via the REST API:

```bash
curl -X POST http://127.0.0.1:8000/nvr/api/detection/104/update-description/ \
     -H "Content-Type: application/json" \
     -d '{"description": "Confirmed courier delivery driver with package. Cleared by security."}'
```

**JSON Response:**
```json
{
  "status": "success",
  "event_id": 104,
  "description": "Confirmed courier delivery driver with package. Cleared by security."
}
```

Once saved, the updated description is immediately queryable across both the **Review** search bar and the **Explore** assistant.
"""
        },
        {
            "title": 'Semantic Search: Explore & Review Workspaces',
            "slug": 'semantic-search-explore-review',
            "category": 'Investigation & Search',
            "order": 8,
            "content_markdown": """# Semantic Search: Explore & Review Workspaces

SemanticEdge provides a unified, dual-workspace investigative experience designed to streamline post-incident forensic analysis:

1. **Review Workspace (`/nvr/review/`)**: Visual object discovery, multi-attribute filtering, category strips, and evidence inspection.
2. **Explore Workspace (`/nvr/explore/`)**: Conversational investigation assistant for conversational querying, track timeline reconstruction, and automated telemetry audits.

---

## Workspace Comparison

| Dimension | Review Workspace (`/nvr/review/`) | Explore Workspace (`/nvr/explore/`) |
|---|---|---|
| **Primary Interaction** | Search bar, filters, category strips, grid | ChatGPT-style conversational thread interface |
| **Best Used For** | Fast visual browsing, multi-attribute filtering | Complex incident queries, track histories, fleet checks |
| **Search Paradigm** | Multi-attribute keyword & token matching | Natural language intent parsing via `AssistantNLPEngine` |
| **Data Presentation** | Detection cards, high-res snapshot modal | Message bubbles, inline snapshot cards, deep links |
| **Page Layout** | Responsive scrollable catalog | Fixed-viewport (dedicated message stream scroll) |

---

## The Review Workspace (`/nvr/review/`)

The Review workspace allows operators to quickly narrow down thousands of recorded detections:

### Multi-Parameter Filter Controls
- **Search Bar**: Tokenized matching across object classes and natural-language AI descriptions.
- **Object Class Filter**: Filter by specific classes (`person`, `car`, `truck`, `bicycle`, etc.).
- **Camera Source**: Filter detections to specific sensors.
- **Datetime Range**: Select explicit "From" and "To" timestamps.

### Category Discovery Strips vs. Filtered Grid
- When viewing **All Classes**, detections are organized into horizontal, scrollable discovery strips grouped by category (Persons, Cars, Trucks, etc.).
- Applying a specific class filter transforms the page into a compact, responsive grid of all matching items.

### Detection Evidence & Details Modal
Clicking anywhere on a detection card opens a responsive, two-column inspection modal:
- **Left Column**: High-resolution evidence snapshot with bounding box.
- **Right Column**: Comprehensive metadata (camera, track ID, confidence, timestamp, intrusion zone), editable AI description, and an **Investigate** button.

---

## The Explore Workspace (`/nvr/explore/`)

The Explore workspace is an internal, in-browser Security Assistant powered by `nvr/assistant/`.

### Fixed-Viewport Architecture
Designed specifically for continuous investigations:
- **Zero Page Scroll**: The header, thread sidebar, and message input composer remain pinned to the viewport.
- **Dedicated Message Stream**: Only the central conversation transcript scrolls.

### Context-Bound Investigations
Clicking **Investigate** on any detection card in Review opens an investigation thread in Explore with that event's context preloaded (camera name, object class, track ID, timestamp, and snapshot).

### Controlled Tool Execution (`NVRTools`)
The assistant never executes raw SQL. Instead, it queries typed class methods in `nvr/assistant/tools.py`:
- `get_latest_intrusion()`: Retrieves the most recent perimeter breach with snapshot.
- `get_track_history(track_id)`: Reconstructs the movement timeline for a specific track ID.
- `get_related_detections(event_id)`: Identifies other objects present around the same time.
- `get_camera_status()`: Summarizes active cameras, day/night modes, and recent events.
- `get_system_telemetry()`: Queries live CPU, RAM, disk usage, and inference targets.
- `get_detection_statistics()`: Computes object breakdowns and hourly activity.

### Example Conversational Queries
```text
> latest intrusion
> alerts for Front Door today
> track history for track 12
> evidence for event 104
> related detections near 19:20
> camera status
> system status
> detection statistics
> monitoring zones
```

### Zero-Dependency Local Intelligence
By default, the assistant runs on `RuleBasedNVRProvider` — an ultra-fast, deterministic local engine requiring **zero external API keys** and zero third-party cloud connections.
"""
        },
        {
            "title": 'Local Video Recording & Evidence Export',
            "slug": 'local-recording-evidence-export',
            "category": 'Storage & Archival',
            "order": 9,
            "content_markdown": """# Local Video Recording & Evidence Export

Preserving tamper-proof forensic evidence while keeping storage consumption manageable is a primary challenge in enterprise surveillance. SemanticEdge combines event-triggered snapshot archiving, browser-compatible video transcoding, and structured CSV telemetry exports.

---

## Evidence Preservation Strategy

```text
Continuous Camera Stream
          │
          ├──► Object Detection / Intrusion Breach Trigger
          │          │
          │          ├──► High-Resolution Snapshot Capture (media/snapshots/<cam_id>/)
          │          │
          │          └──► DetectionEvent Record Logged in Database
          │
          └──► Video Clip Ring Buffer
                     │
                     ▼
            H.264 / MP4 Exporter (media/exports/)
```

---

## Snapshot Evidence Capture

Whenever an object is tracked or breaches a restricted zone, SemanticEdge captures a high-resolution JPEG frame:
- **Storage Location**: `media/snapshots/<camera_id>/`
- **File Naming Convention**: `snap_<camera_id>_<track_id>_<timestamp>.jpg`
- **Database Linkage**: Stored in `DetectionEvent.snapshot_path` for instant retrieval in Review modals and Explore assistant messages.

---

## Video Clip Transcoding (`/nvr/export/`)

Raw camera streams encoded with proprietary or non-standard RTSP codecs often fail to play directly inside modern web browsers.

### Automated H.264 / AVC1 Transcoding
The export engine in `nvr/views.py` ensures that all generated video clips are packaged in web-standard H.264 MP4 containers:

```python
# Video export with FFmpeg fallback
cmd = [
    "ffmpeg", "-y",
    "-i", raw_clip_path,
    "-c:v", "libx264",
    "-preset", "fast",
    "-crf", "23",
    "-pix_fmt", "yuv420p",
    "-movflags", "+faststart",
    output_mp4_path
]
```

- **`yuv420p` Pixel Format**: Ensures universal playback compatibility across Chrome, Safari, Firefox, and mobile browsers.
- **`-movflags +faststart`**: Moves the MP4 index (`moov` atom) to the beginning of the file, allowing instant in-browser playback before the entire file finishes downloading.

---

## Forensic CSV Telemetry Export (`/nvr/export/csv/`)

For legal discovery, compliance audits, or external data analytics, operators can download a complete CSV audit log via `/nvr/export/csv/`.

### Exported CSV Schema:
```csv
timestamp,camera_name,track_id,class_name,confidence,bbox_x1,bbox_y1,bbox_x2,bbox_y2,line_crossing_status,description
2026-10-05 14:15:22,Front Gate,14,person,0.88,142,65,310,480,Intrusion: North Fence,Person walking rapidly along fence
2026-10-05 14:15:24,Driveway South,22,car,0.92,450,210,780,510,,Vehicle entering premises
```

---

## Disk Storage & Retention Management

Surveillance drives will inevitably fill up without proactive disk monitoring. SemanticEdge provides live storage telemetry via the `/nvr/api/system-status/` endpoint:

```json
{
  "disk_percent": 64.2,
  "media_size_mb": 1420.5,
  "snapshots_count": 842,
  "exports_count": 12
}
```

The system status monitor alerts administrators when disk utilization exceeds 85%, allowing automated rotation of the oldest video exports.
"""
        },
        {
            "title": 'Cloud Metadata Storage & Hybrid Edge Architecture',
            "slug": 'cloud-metadata-storage',
            "category": 'Storage & Archival',
            "order": 10,
            "content_markdown": """# Cloud Metadata Storage & Hybrid Edge Architecture

SemanticEdge adopts a modern **Hybrid Edge-Cloud Architecture**. This approach gives enterprise organizations the speed, privacy, and zero-bandwidth cost of edge processing, combined with the centralized management, multi-site aggregation, and high availability of cloud databases.

---

## The Hybrid Paradigm: What Goes Where?

| Data Type | Storage Tier | Location | Rationale |
|---|---|---|---|
| **Raw RTSP Video Feeds** | Local Edge | Edge NVR / On-Premise SSD | Enormous bandwidth (gigabytes per hour); private video never leaves site |
| **High-Res Snapshots** | Local Edge | `media/snapshots/` | Preserves forensic fidelity locally without cloud egress costs |
| **Structured Telemetry** | Cloud / Central DB | PostgreSQL (Render/AWS/etc.) | Tiny payload (kilobytes per day); enables global search and fleet reporting |
| **Assistant Threads** | Cloud / Central DB | `AlertConversation` table | Allows operators to review incident investigations from any device |

---

## Architecture Diagram

```text
+-----------------------------------------------------------+
| Local Edge Station (Site A - Warehouse)                   |
|                                                           |
|  - Cameras & Video Ingestion                              |
|  - YOLOv8 + ByteTrack Inference                           |
|  - High-Res Snapshots stored locally on disk              |
|  - Pushes structured DetectionEvent metadata ──────────+  |
+-------------------------------------------------------│---+
                                                        │
+-------------------------------------------------------│---+
| Local Edge Station (Site B - Lab / Office)            │   |
|                                                       │   |
|  - Cameras & Video Ingestion                          │   |
|  - YOLOv8 + ByteTrack Inference                       │   |
|  - High-Res Snapshots stored locally on disk          │   |
|  - Pushes structured DetectionEvent metadata ─────+   │   |
+---------------------------------------------------│───│---+
                                                    │   │
                                    Lightweight     │   │
                                 JSON / SQL Egress  │   │
                                                    v   v
+-----------------------------------------------------------+
| Central Cloud Database (PostgreSQL on Render / AWS RDS)   |
|                                                           |
|  - Aggregated DetectionEvent records from all sites       |
|  - Global MonitoringZone configurations                   |
|  - Multi-site AlertConversation & ChatMessage threads     |
|  - Web Console Dashboard (accessible to authorized staff) |
+-----------------------------------------------------------+
```

---

## Database Configuration via `DATABASE_URL`

SemanticEdge supports zero-configuration SQLite for standalone edge appliances, and enterprise PostgreSQL for distributed cloud deployments.

Configured simply in `.env`:

### Standalone Edge Mode (Default)
```ini
# Defaults to local SQLite db.sqlite3 when DATABASE_URL is not set
DEBUG=True
```

### Central Cloud PostgreSQL Mode
```ini
DATABASE_URL=postgres://semanticedge_user:SecurePassword123@db.internal.render.com:5432/semanticedge_db
```

In `config/settings.py`, `dj-database-url` automatically parses this connection string and configures connection pooling, SSL encryption, and query optimization.

---

## Key Benefits of Hybrid Cloud Storage

1. **Bandwidth Efficiency**: Even on constrained 4G/5G connections, transmitting lightweight detection rows consumes less than 50 KB/hour, whereas streaming raw 1080p video would consume 1.5 GB/hour.
2. **Absolute Privacy Compliance**: Raw video footage of employees, students, or confidential premises never touches external cloud servers, satisfying GDPR, HIPAA, and institutional data policies.
3. **Resilience to Internet Outages**: If the cloud connection drops, the local edge NVR continues recording and caching events locally, syncing back to the cloud database once connectivity resumes.
"""
        },
        {
            "title": 'Deployment & Production Setup',
            "slug": 'deployment-production-setup',
            "category": 'Deployment & Production',
            "order": 11,
            "content_markdown": """# Deployment & Production Setup

This guide details best practices for deploying SemanticEdge in mission-critical surveillance environments, spanning on-premise edge appliances, cloud-hosted management dashboards, and background daemon services.

---

## Edge Appliance Deployment (On-Premise)

For processing physical camera streams at an edge site, deploy SemanticEdge onto a dedicated hardware appliance:
- **Intel NUC / Mini-PC** (Intel Core i5/i7 with OpenVINO or Vulkan acceleration)
- **NVIDIA Jetson** (Orin Nano / Orin NX with CUDA 11.8+ / TensorRT)
- **Apple Silicon Mac Mini** (M2 / M4 with Metal Performance Shaders)

---

## Production WSGI & Static File Serving

In production, never use `python manage.py runserver`. Run with an enterprise WSGI server like **Gunicorn**:

```bash
gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
```

### Static Asset Hosting via WhiteNoise
SemanticEdge is pre-configured with **WhiteNoise** in `config/settings.py`:
- Serves CSS, JavaScript, and fonts directly from Gunicorn with zero Nginx dependency.
- Automatically creates Gzip and Brotli compressed bundles.
- Employs cache-busting unique hashes (`CompressedManifestStaticFilesStorage`) with 1-year immutable cache headers.

Compile static assets before launch:
```bash
python manage.py collectstatic --noinput
```

---

## Systemd Service Configuration (Linux)

To ensure SemanticEdge boots automatically on system restart and recovers from unexpected process terminations, configure a systemd service:

Create `/etc/systemd/system/semanticedge.service`:

```ini
[Unit]
Description=SemanticEdge AI NVR Service
After=network.target

[Service]
Type=simple
User=surveillance
Group=surveillance
WorkingDirectory=/opt/semanticedge
EnvironmentFile=/opt/semanticedge/.env
ExecStart=/opt/semanticedge/.venv/bin/gunicorn config.wsgi:application \
          --bind 127.0.0.1:8000 \
          --workers 4 \
          --threads 2
Restart=always
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now semanticedge
```

---

## Cloud & PaaS Web Console Deployment (Render)

If hosting the web console and management API in the cloud without local GPU requirements, use the lightweight specification:

### `requirements-render.txt`
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

### Render Build & Start Commands
- **Build Command**:
  ```bash
  pip install -r requirements-render.txt && python manage.py migrate && python seed_demo.py && python manage.py collectstatic --noinput
  ```
- **Start Command**:
  ```bash
  gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
  ```

---

## Production Security Checklist

| Requirement | Implementation Detail | Status |
|---|---|---|
| **Secret Key** | Generate unique 64-character secret in `.env` | Mandatory |
| **Debug Mode** | Ensure `DEBUG=False` in `.env` | Mandatory |
| **Host Headers** | Populate `ALLOWED_HOSTS` with exact domain/IPs | Mandatory |
| **TLS/HTTPS** | Terminate SSL via reverse proxy (Caddy / Nginx / Cloudflare) | Mandatory |
| **Database Security** | Use environment variable `DATABASE_URL` with strong password | Mandatory |
| **Snapshot Permissions** | Restrict read/write permissions on `media/` directory (`chmod 750`) | Mandatory |
| **Credential Rotation** | Change default `admin` and `demo` passwords immediately after seeding | Mandatory |
"""
        },
    ]

    # Clean up outdated documentation pages no longer in the catalogue
    valid_slugs = [d["slug"] for d in docs_data]
    deleted_count, _ = DocPage.objects.exclude(slug__in=valid_slugs).delete()
    if deleted_count:
        print(f"  ✓ Cleaned up {deleted_count} outdated doc page(s)")

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

    print(f"[Seed] Complete! {len(docs_data)} documentation pages seeded successfully.")


if __name__ == "__main__":
    seed()
