# SemanticEdge — Open-Source AI Network Video Recorder (NVR)

<div align="center">

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2%2B-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00599C?logo=yolo&logoColor=white)](https://github.com/ultralytics/ultralytics)
[![Tracking](https://img.shields.io/badge/Tracker-ByteTrack-6D5EF5)](https://github.com/ifzhang/ByteTrack)
[![Tests](https://img.shields.io/badge/Tests-36%20Passing-success.svg)](#-running-tests)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**A high-performance, privacy-first Edge AI Network Video Recorder combining real-time YOLOv8 object detection, ByteTrack tracking, perimeter intrusion alerting, face biometric attendance, industrial counting, and an interactive Telegram Security Assistant.**

[Features](#-key-features) • [Quickstart](#-quickstart-guide) • [Telegram Assistant](#-telegram-security-assistant) • [Architecture](#-system-architecture) • [Supported Classes](#-supported-classes) • [Cloud Deployment](#-cloud--lightweight-deployment-render) • [Documentation](#-documentation--api)

</div>

---

## 🚀 Overview

**SemanticEdge** is an enterprise-grade, open-source NVR designed for perimeter security, traffic monitoring, biometric attendance, and industrial operations. Unlike cloud-dependent surveillance platforms, SemanticEdge processes all video streams **strictly on local hardware** — your raw camera streams, biometrics, and detection telemetry never leave your private network perimeter.

By coupling **Ultralytics YOLOv8** neural network inference with **ByteTrack** multi-object tracking, SemanticEdge converts dumb video feeds into an intelligent, queryable event stream with persistent identities, trajectory trails, monitoring zones, and structured audit logs.

---

## ✨ Key Features

### 🖥️ Professional NVR Console
* **Slim Vertical Navigation Rail**: Fast keyboard-friendly tab switching between Live Grid, Focus View, Review, Explore, Export, Face Recognition, Object Counter, and Settings.
* **Multi-Camera Management**: Run single-camera focus or 2x2/4-up live grid feeds simultaneously. Soft-delete camera logic ensures all historical detections and track IDs remain intact if a camera is re-added.
* **Persistent Telemetry Status Bar**: Real-time system monitoring displaying CPU %, RAM %, Inference Engine (`CPU` / `CUDA 0` / `Apple MPS`), Feed FPS, Active Cameras count, and pulsing green System Health indicator.
* **Obsidian Ethereal Design System**: Dark-mode glassmorphism interface built with vanilla CSS tokens, Inter typography, and JetBrains Mono telemetry labels.

### 🛡️ Perimeter Intrusion & Monitoring Zones
* **Dynamic Zone Configuration**: Define custom polygon restricted zones and line tripwires directly on camera coordinates.
* **Normalized Resolution Mapping**: Normalized `[[x, y], ...]` vertices map seamlessly across varying camera resolutions (1080p, 4K, 720p).
* **Instant Automatic Alerting**: Restricted area breaches immediately log `DetectionEvent` records and dispatch rich CCTV notifications.

### 🤖 Telegram Security Assistant & OpenClaw NLP
* **Interactive Operator Authentication**: Dedicated `/start` and `/login <username> <password>` flow validating credentials against Django's `auth_user` database. Unauthenticated access to surveillance telemetry is strictly blocked.
* **Natural Language Surveillance Queries**:
  - `latest intrusion`: Immediate snapshot evidence and breach report.
  - `alerts today` / `alerts for Front Door`: Filtered event summaries.
  - `evidence for track 5` / `event 102`: Target snapshot retrieval.
  - `camera status`: Fleet status, active streams, day/night mode.
  - `system status`: Live CPU, RAM, disk storage, and media archive size.
  - `detection statistics`: Classification breakdown and frequency.
  - `monitoring zones`: Active tripwires and polygon zones.
  - `export requests`: Recent video exports and status.
* **Helpful Fallback**: Unrecognized queries receive structured recommendations instead of rejection messages.
* **Persistent User Feedback Loop**: Every completed operational query prompts for feedback (`YES`/`NO`), recorded into the database (`TelegramFeedback`) for auditing.
* **Professional CCTV Formatting**: Strictly zero emojis — formatted with clean ASCII borders and fixed-width headers.

### 👤 Face Recognition & Biometric Attendance
* **Reference Enrollment**: Upload reference photos (`FaceReference`) with employee/student IDs and department metadata.
* **Real-Time Matching**: Automated face matching with confidence scoring and timestamped attendance records (`AttendanceRecord`).

### 🏭 Industrial Conveyor & Object Counter
* **Line-Crossing Analytics**: Count objects crossing bidirectional threshold boundaries (IN/OUT).
* **Conveyor Rate Tracking**: Real-time rate-per-minute throughput calculation with structured logging (`ObjectCountRecord`).

### 📦 Evidence Exporter & Video Transcoding
* **H.264 / AVC1 Video Clips**: Browser-playable MP4 video export with automatic FFmpeg transcoding fallback.
* **Snapshot Gallery**: High-resolution detection frame captures linked by Track ID.
* **CSV Telemetry Export**: One-click download of all detection logs with bounding boxes, confidence, and timestamps (`/nvr/export/csv/`).

---

## 🏗️ System Architecture

```
                                  ┌───────────────────────────┐
                                  │       Video Sources       │
                                  │  (USB / RTSP IP Cameras)  │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  Edge AI Inference & Tracking Pipeline (src/)                                           │
│                                                                                         │
│  ┌────────────────────────┐      ┌────────────────────────┐      ┌───────────────────┐  │
│  │   detector.py          │      │   tracker.py           │      │   trajectory.py   │  │
│  │   YOLOv8 FP32/FP16     ├─────►│   ByteTrack Tracking   ├─────►│   30-Point Temporal   │
│  │   Target Class Filter  │      │   Kalman + Association │      │   Path Buffer     │  │
│  └────────────────────────┘      └────────────────────────┘      └─────────┬─────────┘  │
│                                                                            │            │
│  ┌────────────────────────┐      ┌────────────────────────┐                │            │
│  │   logger.py            │      │   draw_utils.py        │◄───────────────┘            │
│  │   Structured CSV Audit │◄─────┤   BBox & Label Overlay │                             │
│  └────────────────────────┘      └───────────┬────────────┘                             │
└──────────────────────────────────────────────┼──────────────────────────────────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  Django Application Core (nvr/, core/, docs/, accounts/)                                │
│                                                                                         │
│  ┌────────────────────────┐      ┌────────────────────────┐      ┌───────────────────┐  │
│  │   streaming.py         │      │   models.py            │      │   openclaw.py     │  │
│  │   MJPEG Multi-Camera   │      │   Camera, Event,       │      │   Security Assistant  │  │
│  │   Intrusion Evaluator  │      │   Zone, Face, Feedback │      │   OpenClaw NLP Engine │  │
│  └───────────┬────────────┘      └───────────┬────────────┘      └─────────┬─────────┘  │
└──────────────┼───────────────────────────────┼─────────────────────────────┼────────────┘
               │                               │                             │
               ▼                               ▼                             ▼
  ┌────────────────────────┐      ┌────────────────────────┐    ┌────────────────────────┐
  │  Client Browser View   │      │  SQLite / PostgreSQL   │    │  Telegram Bot Poller   │
  │  (Zero Plugins / HTML5)│      │  Detection & Telemetry │    │  (Single Update Daemon)│
  └────────────────────────┘      └────────────────────────┘    └────────────────────────┘
```

---

## 🎯 Supported Classes

SemanticEdge filters standard COCO-80 object detections into **6 primary security and vehicle classes**, alongside custom biometric face profiles:

| Class Name | COCO ID | Color Code | Hex Value | Primary Surveillance Application |
|---|:---:|:---:|:---:|---|
| **`person`** | `0` | Amber | `#ffa856` | Perimeter intrusion, pedestrian tracking, line crossing |
| **`bicycle`** | `1` | Cyan | `#3cc8ff` | Bike lane & sidewalk monitoring |
| **`car`** | `2` | Lime | `#a0ff3c` | Vehicle access, parking, traffic analysis |
| **`motorcycle`** | `3` | Magenta | `#c850ff` | Two-wheeler traffic counting & unauthorized entry |
| **`bus`** | `5` | Yellow | `#ffc850` | Public transit bays & terminal monitoring |
| **`truck`** | `7` | Blue | `#5082ff` | Commercial loading bays & freight logistics |
| **`Face Reference`** | Custom | Violet | `#a855f7` | Biometric attendance & staff/student recognition |

---

## ⚡ Quickstart Guide

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/your-username/semanticedge.git
cd semanticedge

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Configure your .env file:
# TELEGRAM_BOT_TOKEN=your_bot_token
# TELEGRAM_CHAT_ID=your_chat_id
# YOLO_DEVICE=cpu (or '0' for CUDA, 'mps' for Apple Silicon)
```

### 3. Initialize Database & Seed Documentation

```bash
# Run database migrations
python manage.py migrate

# Seed demo users, default camera, and 9 documentation pages
python seed_demo.py
```

### 4. Launch Development Server

```bash
# Terminal 1: Launch Web & NVR Application
python manage.py runserver 127.0.0.1:8000
```

Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

#### Demo Credentials:
| Role | Username | Password |
|---|---|---|
| **Administrator** | `admin` | `admin123` |
| **Standard User** | `demo` | `demo123` |

### 5. Launch Telegram Security Assistant (Optional)

```bash
# Terminal 2: Launch Telegram Bot Long-Polling Daemon
python manage.py run_openclaw_bot
```

---

## 🤖 Telegram Security Assistant

The Telegram integration serves as an interactive **SemanticEdge Security Assistant**:

### Authentication Flow
1. Send `/start` to the bot.
2. Bot requests: `Please enter your NVR username to authenticate:`.
3. Enter your username (e.g. `admin`).
4. Enter your password (e.g. `admin123`).
5. Upon successful authentication, your session is linked and capabilities are displayed.
6. Alternatively, log in instantly via `/login <username> <password>`.
7. End session anytime with `/logout`.

### Operational Query Examples
```text
> latest intrusion
> alerts today
> alerts for Front Door
> evidence for track 5
> event 104
> camera status
> system status
> detection statistics
> monitoring zones
> export requests
```

### Interactive Feedback Loop
Following every served operational query, the assistant prompts:
```text
Was this information helpful? (Reply YES or NO)
```
Replying `YES` or `NO` saves telemetry to the `TelegramFeedback` database table.

---

## ☁️ Cloud & Lightweight Deployment (Render)

For web dashboard hosting, API evaluation, or demo instances without heavy GPU/CUDA dependencies, SemanticEdge includes a lightweight deployment specification:

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

### Render / PaaS Build & Start Commands:
- **Build Command**:
  ```bash
  pip install -r requirements-render.txt && python manage.py migrate && python seed_demo.py && python manage.py collectstatic --noinput
  ```
- **Start Command**:
  ```bash
  gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
  ```

---

## 📂 Project Structure

```
semanticedge/
├── manage.py                           # Django management CLI
├── requirements.txt                    # Full Edge AI dependencies (PyTorch, YOLOv8, OpenCV)
├── requirements-render.txt             # Lightweight PaaS/web deployment dependencies
├── .env.example                        # Environment variable configuration template
├── seed_demo.py                        # Database seeder (users, cameras, 9 DocPages)
├── LICENSE                             # Apache 2.0 Open Source License
├── CONTRIBUTING.md                     # Contributor standards & PR workflow
│
├── config/                             # Django Project Configuration
│   ├── settings.py                     # Decouple configuration, auth, static paths
│   ├── urls.py                         # Root URL routing
│   ├── wsgi.py / asgi.py               # WSGI/ASGI gateways
│
├── src/                                # Core Edge AI Inference Engine
│   ├── detector.py                     # YOLOv8 detection wrapper
│   ├── tracker.py                      # YOLOv8 + ByteTrack persistent tracker
│   ├── trajectory.py                   # 30-point temporal trajectory store
│   ├── draw_utils.py                   # Bounding box & label drawing utilities
│   ├── logger.py                       # Structured CSV detection logger
│   └── main.py                         # Standalone OpenCV entrypoint
│
├── nvr/                                # NVR SaaS Application
│   ├── models.py                       # Camera, DetectionEvent, MonitoringZone,
│   │                                   # FaceReference, AttendanceRecord,
│   │                                   # ObjectCountRecord, TelegramSession, TelegramFeedback
│   ├── views.py                        # Live, Focus, Review, Explore, Export,
│   │                                   # Face Recognition, Object Counter, Settings
│   ├── streaming.py                    # MJPEG multi-camera & zone intrusion generator
│   ├── openclaw.py                     # OpenClaw NLP Engine & Telegram Assistant
│   ├── management/commands/
│   │   └── run_openclaw_bot.py         # Telegram polling daemon
│   ├── urls.py                         # NVR tab routes & REST endpoints
│   └── tests.py                        # 26 automated unit tests
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
    ├── accounts/login.html             # Standalone sign-in template
    ├── docs/                           # Documentation list & detail templates
    └── nvr/                            # NVR Console Views
        ├── base_nvr.html               # NVR master shell (Left rail + Telemetry bar)
        ├── live.html                   # Multi-camera grid live feed
        ├── camera_focus.html           # Single camera AI focus view
        ├── review.html                 # Event review timeline & density bar
        ├── explore.html                # Category object discovery strips
        ├── export.html                 # Evidence exporter & H.264 video player
        ├── face_recognition.html       # Biometric face profile management
        ├── object_counter.html         # Industrial conveyor line-crossing
        ├── settings.html               # Camera & Telegram alert test button
        └── log.html                    # CSV detection log viewer
```

---

## ⚙️ Hardware Acceleration

SemanticEdge supports configurable compute backends via the `YOLO_DEVICE` variable in `.env`:

### 1. CPU (Default)
Optimized for standard x86 and ARM processors:
```ini
YOLO_DEVICE=cpu
```

### 2. NVIDIA CUDA GPU
For workstations and servers equipped with NVIDIA GPUs:
```ini
YOLO_DEVICE=0
```

### 3. Apple Silicon (M1/M2/M3/M4)
Utilizes Apple Metal Performance Shaders (MPS):
```ini
YOLO_DEVICE=mps
```

---

## 🧪 Running Tests

SemanticEdge includes a comprehensive automated test suite testing routes, permissions, markdown rendering, camera isolation, Telegram authentication, NLP query parsing, and feedback recording:

```bash
# Run all test suites across all applications
python manage.py test accounts core docs nvr

# Verbose test execution
python manage.py test accounts core docs nvr -v 2
```

**Test Coverage**: 36 automated unit tests covering all core modules, access control, and edge AI services.

---

## 🤝 Contributing

Contributions are welcome! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) guide for details on our code of conduct, branch conventions, and pull request workflow.

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.
