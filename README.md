<div align="center">

# 🎯 SemanticEdge

### Enterprise-Grade AI NVR · Perimeter Security · Internal Investigation Workspace

**YOLOv8 + ByteTrack · Django · Intrusion Detection · Internal Security Assistant**

</div>

---

## 🚀 Overview

**SemanticEdge** is an open-source, enterprise-grade Network Video Recorder (NVR) designed for perimeter security, traffic monitoring, and industrial operations. All video processing runs **entirely on local hardware** — raw camera streams, detection telemetry, and investigation workflows never leave your private network.

By coupling **Ultralytics YOLOv8** neural network inference with **ByteTrack** multi-object tracking, SemanticEdge converts dumb video feeds into an intelligent, queryable event stream — with persistent object identities, trajectory trails, configurable restricted monitoring zones, and a fully integrated in-browser Security Assistant for historical investigation.

---

## ✨ Key Features

### 🖥️ Professional NVR Console
- **Slim Vertical Navigation Rail**: Fast tab switching between Live Grid, Tracker (Restricted Area), Review, Explore, Logs, Export, and Settings.
- **Multi-Camera Management**: Run single-camera focus or multi-up live grid feeds simultaneously. Soft-delete camera logic preserves all historical detections if a camera is re-added.
- **Persistent Telemetry Status Bar**: Real-time monitoring — CPU %, RAM %, Inference Engine (`CPU` / `CUDA 0` / `Apple MPS`), Feed FPS, Active Camera count, and pulsing System Health indicator.
- **Obsidian Ethereal Design System**: Dark-mode glassmorphism interface built with vanilla CSS design tokens, Inter typography, and JetBrains Mono telemetry labels.

### 🛡️ Perimeter Intrusion & Restricted Zone Monitoring
- **Dynamic Zone Configuration**: Draw and configure custom polygon restricted zones and line tripwires directly mapped to camera pixel coordinates.
- **Normalized Resolution Mapping**: `[[x, y], ...]` vertices normalize seamlessly across varying camera resolutions (720p, 1080p, 4K).
- **Non-Blocking Intrusion Logging**: Restricted area breaches immediately log a `DetectionEvent` record with `line_crossing_status`, camera name, snapshot path, and bounding box — fully decoupled from the streaming pipeline so detection is never stalled.
- **In-Browser Alert Toasts**: Live intrusion notifications delivered directly to the browser via the `/nvr/api/alerts/latest/` polling endpoint — no Telegram or external messaging required.

### 🔍 Event Review & Object Discovery (`/nvr/review/`)
- **Multi-Parameter Search**: Filter historical detections by keyword or natural-language description, object class, camera source, and datetime range simultaneously.
- **Category Discovery Strips**: Object cards grouped and displayed as horizontal scrollable strips per class (Persons, Cars, Trucks, Bicycles, Motorcycles, Buses).
- **Filtered Grid View**: Selecting a class filter switches the layout to a full responsive grid of all matched detections.
- **Clickable Detection Cards**: Click anywhere on a card to open the **Detection Evidence & Details** modal — displaying the evidence snapshot, bounding box metadata, track ID, confidence score, and editable AI description.
- **Deep-Link Navigation**: Every detection card includes a direct **Investigate** button that opens the Security Assistant workspace pre-loaded with that event's context.

### 🤖 Internal Security Assistant (`/nvr/explore/`)
- **ChatGPT-Style Investigation Workspace**: Full-page, fixed-viewport layout with a persistent thread sidebar, scrollable message stream, and pinned composer — no page-level scroll.
- **Thread-Based Investigations**: Each investigation thread is tied to a `DetectionEvent` or camera context. Threads are created, listed, continued, and deleted from the sidebar without leaving the workspace.
- **Context-Aware Conversations**: Selecting a detection event from Review or clicking a card in the Live view binds it to the active investigation thread. The assistant receives the event's class, track ID, camera, timestamp, and snapshot path as structured context.
- **Controlled Tool Execution**: The assistant invokes typed tool functions (`NVRTools` in `nvr/assistant/tools.py`) for all data retrieval — it never constructs raw SQL or accesses the database directly.
- **Pluggable LLM Provider**: `AssistantService` uses a `BaseLLMProvider` abstraction. The default is `RuleBasedNVRProvider` — a zero-dependency, deterministic NLP engine requiring no API keys. The architecture supports swapping in a Gemini or other LLM provider.
- **Starter Prompts & Quick Pills**: Context-aware starter suggestions and quick query chips help operators begin investigations immediately.
- **Evidence Rendering**: Snapshot images, camera details, and Review deep-links appear inline inside assistant responses.

### 🏭 Object Counter & Restricted Area Tracker
- **Line-Crossing Analytics**: Count objects crossing bidirectional threshold boundaries (IN/OUT).
- **Conveyor Rate Tracking**: Real-time throughput calculation with structured `ObjectCountRecord` logging.
- **Zone-Specific Class Targeting**: Each monitoring zone can be configured to monitor only specific object classes.

### 📦 Evidence Exporter
- **H.264 / AVC1 Video Clips**: Browser-playable MP4 video export with automatic FFmpeg transcoding fallback.
- **Snapshot Gallery**: High-resolution detection frame captures linked by Track ID.
- **CSV Telemetry Export**: One-click download of all detection logs with bounding boxes, confidence, and timestamps (`/nvr/export/csv/`).

### 📝 Model-Driven Documentation
- **Markdown Documentation Engine**: Operator documentation stored as `DocPage` model records, rendered to HTML with Pygments syntax highlighting.

---

## 🏗️ System Architecture

```
                              +-----------------------------------+
                              |          Video Sources            |
                              |   (USB Webcam / RTSP IP Camera)  |
                              +------------------+----------------+
                                                 |
                                                 v
+--------------------------------------------------------------------------------+
|  Edge AI Inference & Tracking Pipeline  (nvr/streaming.py + src/)              |
|                                                                                |
|  +---------------------+    +---------------------+    +--------------------+ |
|  |  YOLOv8 Inference   |    |  ByteTrack Tracking  |    |  Trajectory Store  | |
|  |  (FP32 / FP16)      +--->|  Kalman + Hungarian  +--->|  30-pt Path Buffer | |
|  |  Class Filter       |    |  Persistent Track ID |    |                    | |
|  +---------------------+    +---------------------+    +----------+---------+ |
|                                                                    |           |
|                        MonitoringZone Intersection Check           |           |
|                                   --> Intrusion Detected?          |           |
|                                              |                     |           |
|                                       Yes -->+                     |           |
|                                              v                                 |
|                                 DetectionEvent persisted                       |
|                          (class, track_id, camera, snapshot,                   |
|                           bbox, line_crossing_status)                          |
+--------------------------------------------------------------------------------+
                                                 |
                                                 v
+--------------------------------------------------------------------------------+
|  Django Application Core  (nvr/, accounts/, docs/, core/)                      |
|                                                                                |
|  +-----------------+    +------------------+    +---------------------------+  |
|  |  Live View      |    |  Review Tab      |    |  Explore Tab              |  |
|  |  (MJPEG Stream  |    |  (Object Search  |    |  (Internal Security       |  |
|  |  + Zone Config) |    |  & Discovery)    |    |  Assistant Workspace)     |  |
|  +-----------------+    +--------+---------+    +-------------+-------------+  |
|                                  |                            |                |
|                     Deep-link: event_id / track_id            |                |
|                                  +--------------->------------+                |
|                                                                                |
|  +--------------------------------------------------------------------------+  |
|  |  Internal Security Assistant Service  (nvr/assistant/)                   |  |
|  |                                                                           |  |
|  |  AssistantService (service.py)                                            |  |
|  |    +-- AssistantNLPEngine (nlp.py)  -- intent parsing                    |  |
|  |    +-- NVRTools (tools.py)          -- controlled, typed data access      |  |
|  |    +-- BaseLLMProvider (llm.py)     -- RuleBasedNVRProvider (default)     |  |
|  |                                                                           |  |
|  |  Models: AlertConversation, ChatMessage                                   |  |
|  +--------------------------------------------------------------------------+  |
+--------------------------------------------------------------------------------+
                                                 |
                          +----------------------+----------------------+
                          v                      v                     v
            +---------------------+  +------------------+  +------------------+
            |  Client Browser     |  |  SQLite /        |  |  Media Storage   |
            |  (Vanilla HTML5/JS) |  |  PostgreSQL      |  |  (snapshots,     |
            +---------------------+  +------------------+  |   video clips)   |
                                                           +------------------+
```

---

## 📐 Workspace Design

SemanticEdge has two clearly separated investigation workspaces:

| Workspace | URL | Purpose |
|---|---|---|
| **Review** | `/nvr/review/` | Historical object search & discovery. Multi-parameter filtering, category strips, detection cards with evidence modals. |
| **Explore** | `/nvr/explore/` | Internal Security Assistant. Thread-based investigation, NLP query engine, context-bound conversations, evidence rendering. |

The two workspaces are deeply linked: every detection card in Review has an **Investigate** button that opens Explore pre-loaded with that event. Conversely, the assistant can navigate back to the Review timeline for any track it references.

---

## 🎯 Supported Detection Classes

SemanticEdge filters standard COCO-80 object detections into **6 primary security and vehicle classes**:

| Class | COCO ID | Color | Primary Application |
|---|:---:|:---:|---|
| `person` | `0` | Amber `#ffa856` | Perimeter intrusion, pedestrian tracking, line crossing |
| `bicycle` | `1` | Cyan `#3cc8ff` | Bike lane & sidewalk monitoring |
| `car` | `2` | Lime `#a0ff3c` | Vehicle access, parking, traffic analysis |
| `motorcycle` | `3` | Magenta `#c850ff` | Two-wheeler traffic counting |
| `bus` | `5` | Yellow `#ffc850` | Public transit bay monitoring |
| `truck` | `7` | Blue `#5082ff` | Commercial loading bays & freight |

---

## ⚡ Quickstart Guide

### 1. Clone & Setup Environment

```bash
git clone https://github.com/your-username/semanticedge.git
cd semanticedge

python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` to configure:

```ini
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# YOLOv8 model and inference settings
YOLO_MODEL_PATH=yolov8n.pt
YOLO_CONF_THRESHOLD=0.40
YOLO_DEVICE=cpu         # 'cpu', '0' for CUDA GPU, 'mps' for Apple Silicon
```

### 3. Initialize Database & Seed Demo Data

```bash
python manage.py migrate
python seed_demo.py
```

### 4. Launch Development Server

```bash
python manage.py runserver 127.0.0.1:8000
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

#### Demo Credentials:
| Role | Username | Password |
|---|---|---|
| **Administrator** | `admin` | `admin123` |
| **Standard User** | `demo` | `demo123` |

---

## 🤖 Internal Security Assistant

The Security Assistant runs entirely inside the browser at `/nvr/explore/`. It requires no external API keys, bot tokens, or messaging accounts.

### How It Works

1. Click **Explore** in the left navigation rail.
2. Start a new investigation thread, or click **Investigate** on any detection card in Review.
3. The assistant receives structured context (event class, track ID, camera, timestamp, snapshot) and opens an investigation thread.
4. Type a natural-language query in the composer. The assistant parses intent via `AssistantNLPEngine` and executes the appropriate `NVRTools` function.

### Example Queries

```
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

### Architecture

```
User Message --> AssistantNLPEngine (intent parsing)
                     |
                     v
              NVRTools (controlled DB queries)
                     |
                     v
              BaseLLMProvider.respond()
              [RuleBasedNVRProvider by default -- zero external dependencies]
                     |
                     v
              ChatMessage saved --> returned to browser
```

All query results are routed through typed `NVRTools` class methods — the LLM provider never constructs raw SQL or directly accesses the database.

---

## ⚙️ Hardware Acceleration

SemanticEdge supports configurable compute backends via `YOLO_DEVICE` in `.env`:

| Backend | Config | Use Case |
|---|---|---|
| CPU (Default) | `YOLO_DEVICE=cpu` | Standard x86/ARM processors |
| NVIDIA CUDA | `YOLO_DEVICE=0` | NVIDIA GPU workstations |
| Apple Silicon | `YOLO_DEVICE=mps` | Apple M1/M2/M3/M4 (Metal) |

---

## ☁️ Cloud & Lightweight Deployment (Render / PaaS)

For web dashboard hosting or demo instances without GPU/CUDA dependencies:

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

### Build & Start Commands

```bash
# Build
pip install -r requirements-render.txt && python manage.py migrate && python seed_demo.py && python manage.py collectstatic --noinput

# Start
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

---

## 📂 Project Structure

```
semanticedge/
├── manage.py                           # Django management CLI
├── requirements.txt                    # Full edge AI dependencies (PyTorch, YOLOv8, OpenCV)
├── requirements-render.txt             # Lightweight PaaS/web deployment dependencies
├── .env.example                        # Environment variable configuration template
├── seed_demo.py                        # Database seeder (users, cameras, demo detections)
├── LICENSE                             # Apache 2.0 Open Source License
├── CONTRIBUTING.md                     # Contributor standards & PR workflow
│
├── config/                             # Django Project Configuration
│   ├── settings.py                     # Decouple configuration, auth, static paths
│   ├── urls.py                         # Root URL routing
│   └── wsgi.py / asgi.py               # WSGI/ASGI gateways
│
├── src/                                # Core Edge AI Inference Engine
│   ├── detector.py                     # YOLOv8 detection wrapper
│   ├── tracker.py                      # ByteTrack persistent multi-object tracker
│   ├── trajectory.py                   # 30-point temporal trajectory buffer
│   ├── draw_utils.py                   # Bounding box & label overlay utilities
│   ├── logger.py                       # Structured CSV detection logger
│   └── main.py                         # Standalone OpenCV entrypoint
│
├── nvr/                                # NVR Application
│   ├── models.py                       # Camera, DetectionEvent, MonitoringZone,
│   │                                   # ObjectCountRecord, AlertConversation, ChatMessage
│   ├── views.py                        # LiveView, ReviewView, ExploreView, ExportView,
│   │                                   # ObjectCounterView, SettingsView,
│   │                                   # AssistantConversationApiView (& related),
│   │                                   # LatestIntrusionsApiView, SystemStatusApiView, ...
│   ├── streaming.py                    # MJPEG multi-camera & zone intrusion generator
│   ├── urls.py                         # NVR page routes & REST API endpoints
│   ├── tests.py                        # 35 automated unit & integration tests
│   └── assistant/                      # Internal Security Assistant Service
│       ├── __init__.py
│       ├── service.py                  # AssistantService (conversations, context, tools)
│       ├── tools.py                    # NVRTools — typed controlled data access layer
│       ├── llm.py                      # BaseLLMProvider, RuleBasedNVRProvider
│       └── nlp.py                      # AssistantNLPEngine — intent parsing
│
├── accounts/                           # User Authentication & Profiles
│   ├── views.py                        # Custom sign-in & registration
│   ├── urls.py                         # Auth routes
│   └── tests.py                        # Authentication test suite
│
├── docs/                               # Model-Driven Documentation Engine
│   ├── models.py                       # DocPage model (Markdown storage)
│   ├── views.py                        # Markdown to HTML compiler with Pygments
│   ├── admin.py                        # Django admin Markdown editor
│   └── tests.py                        # Documentation rendering tests
│
├── core/                               # Public Marketing Application
│   ├── views.py                        # Landing page view
│   ├── urls.py                         # Marketing routes
│   └── tests.py                        # Landing page tests
│
├── static/                             # Static Assets
│   ├── css/design.css                  # Ethereal Precision unified design system
│   └── js/main.js                      # Telemetry pollers, modals & interactions
│
└── templates/                          # HTML5 Templates
    ├── base.html                       # Public marketing master shell
    ├── accounts/login.html             # Sign-in template
    ├── docs/                           # Documentation list & detail templates
    └── nvr/                            # NVR Console Views
        ├── base_nvr.html               # NVR master shell (sidebar + telemetry bar + assistant modal)
        ├── live.html                   # Multi-camera live grid with zone config panel
        ├── review.html                 # Event Review & Object Discovery workspace
        ├── explore.html                # ChatGPT-style Internal Security Assistant workspace
        ├── restricted_area.html        # Object Counter & Restricted Area Tracker
        ├── export.html                 # Evidence exporter & H.264 video player
        ├── settings.html               # Camera settings & Assistant diagnostics
        └── log.html                    # Detection event log viewer
```

---

## 🗄️ Data Models

| Model | App | Description |
|---|---|---|
| `Camera` | `nvr` | Camera config — source URL, YOLO device, night threshold |
| `DetectionEvent` | `nvr` | Single detected object — class, track ID, bbox, snapshot, intrusion status |
| `MonitoringZone` | `nvr` | Polygon/line zone config per camera |
| `ObjectCountRecord` | `nvr` | IN/OUT line-crossing count record |
| `AlertConversation` | `nvr` | A Security Assistant investigation thread |
| `ChatMessage` | `nvr` | Individual assistant conversation message (user or assistant role) |

---

## 🔌 REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/nvr/api/system-status/` | CPU, RAM, GPU stats, camera fleet status |
| `GET` | `/nvr/api/alerts/latest/` | Recent intrusion events for browser toast notifications |
| `GET/POST` | `/nvr/api/camera/<id>/zones/` | List or save monitoring zones for a camera |
| `POST` | `/nvr/api/camera/<id>/night-threshold/` | Update camera night-mode threshold |
| `POST` | `/nvr/api/detection/<id>/update-description/` | Update natural-language AI description |
| `POST` | `/nvr/api/detection/<id>/delete/` | Delete a detection event record |
| `GET/POST` | `/nvr/api/assistant/conversations/` | List or create investigation threads |
| `GET/DELETE` | `/nvr/api/assistant/conversations/<id>/` | Retrieve or delete a thread |
| `POST` | `/nvr/api/assistant/conversations/<id>/messages/` | Post a message to a thread |
| `GET/POST` | `/nvr/api/assistant/diagnostics/` | Assistant health status & provider info |

---

## 🧪 Running Tests

SemanticEdge maintains a comprehensive automated test suite covering routes, access control, assistant service logic, controlled tool execution, conversation management, API endpoints, Review search filtering, and Explore workspace rendering:

```bash
# Run all tests
python manage.py test

# Verbose output
python manage.py test -v 2
```

**Test Coverage**: 35 automated tests, 0 failures. Zero Django system check issues.

---

## 🤝 Contributing

Contributions are welcome! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) guide for details on our code of conduct, branch conventions, and pull request workflow.

---

## 📄 License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.
