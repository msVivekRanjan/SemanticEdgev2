# SemanticEdge — Open-Source AI Network Video Recorder (NVR)

<div align="center">

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2%2B-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-00599C?logo=yolo&logoColor=white)](https://github.com/ultralytics/ultralytics)
[![Tracking](https://img.shields.io/badge/Tracker-ByteTrack-6D5EF5)](https://github.com/ifzhang/ByteTrack)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**A high-performance, privacy-first edge AI Network Video Recorder combining real-time YOLOv8 object detection, ByteTrack multi-object tracking, and a sleek Obsidian dark-mode monitoring console.**

[Features](#-key-features) • [Quickstart](#-quickstart-guide) • [Architecture](#-system-architecture) • [Supported Classes](#-supported-object-classes) • [Hardware Acceleration](#-hardware-acceleration) • [Documentation](#-documentation--api)

</div>

---

## 🚀 Overview

**SemanticEdge** is an open-source NVR designed for physical security, traffic monitoring, and perimeter surveillance. Unlike cloud-dependent CCTV systems, SemanticEdge processes all video streams **strictly on local hardware**. Your camera feeds and detection telemetry never leave your network perimeter.

By coupling **Ultralytics YOLOv8** neural network inference with **ByteTrack** multi-object tracking, SemanticEdge converts dumb video feeds into an intelligent, queryable event stream with persistent identities, trajectory trails, and structured audit logs.

---

## ✨ Key Features

### 🖥️ Professional NVR Console
* **Slim Vertical Navigation Rail**: Fast keyboard-friendly tab switching between Live, Review, Explore, Export, and Settings.
* **Persistent Telemetry Status Bar**: Real-time system monitoring displaying CPU %, RAM %, Inference Engine (`CPU` / `CUDA 0` / `Apple MPS`), Feed FPS, Active Cameras count, and pulsing green System Health indicator.
* **Obsidian Ethereal Design System**: Dark-mode glassmorphism interface built with vanilla CSS tokens, Inter typography, and JetBrains Mono data labels.

### 📹 Multi-Modal Video & Tracking Pipeline
* **Live Video Monitor**: Ultra low-latency MJPEG-over-HTTP stream (`multipart/x-mixed-replace`) with live bounding boxes, track IDs, confidence scores, and real-time FPS overlay.
* **Event Review Timeline**: Chronological event gallery with snapshots, relative timestamps (*"2m ago"*), camera/class filters, and a vertical density strip for jumping to specific hours.
* **Object-Class Exploration**: Query detections grouped by object categories (**Persons**, **Cars**, **Bicycles**, **Trucks**, **Motorcycles**, **Buses**) with interactive detail modals displaying coordinates, center points, and line-crossing status.
* **Evidence Exporter**: Time-range clip trimming, JPEG snapshot extraction, and download history repository.
* **Structured Event Logging**: Auto-rotating CSV telemetry logging frame numbers, bounding box coordinates `[x1, y1, x2, y2]`, confidence scores, and trajectory history.

---

## 🏗️ System Architecture

```
                                  ┌───────────────────────────┐
                                  │      Video Sources        │
                                  │ (USB Webcams / IP RTSP)   │
                                  └─────────────┬─────────────┘
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  AI Inference & Tracking Pipeline (src/)                                                │
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
│  Django Web & NVR Application Layer (nvr/, core/, docs/, accounts/)                    │
│                                                                                         │
│  ┌────────────────────────┐      ┌────────────────────────┐      ┌───────────────────┐  │
│  │   streaming.py         │      │   views.py             │      │   base_nvr.html   │  │
│  │   MJPEG Generator      ├─────►│   Live / Review /      ├─────►│   Slim Rail +     │  │
│  │   (multipart boundary) │      │   Explore / Export     │      │   Telemetry Bar   │  │
│  └────────────────────────┘      └────────────────────────┘      └───────────────────┘  │
└──────────────────────────────────────────────┬──────────────────────────────────────────┘
                                               │
                                               ▼
                                  ┌───────────────────────────┐
                                  │    Client Browser View    │
                                  │  (No Plugins / No WebRTC) │
                                  └───────────────────────────┘
```

---

## 🎯 Supported Object Classes

SemanticEdge filters standard COCO-80 object detections into **6 primary security and vehicle classes**:

| Class Name | COCO ID | Color Code | Hex Value | Primary Application |
|---|:---:|:---:|:---:|---|
| **`person`** | `0` | Amber | `#ffa856` | Perimeter intrusion, pedestrian tracking |
| **`bicycle`** | `1` | Cyan | `#3cc8ff` | Bike lane & sidewalk monitoring |
| **`car`** | `2` | Lime | `#a0ff3c` | Vehicle access & parking management |
| **`motorcycle`** | `3` | Magenta | `#c850ff` | Two-wheeler traffic counting |
| **`bus`** | `5` | Yellow | `#ffc850` | Public transit & terminal monitoring |
| **`truck`** | `7` | Blue | `#5082ff` | Commercial loading bay & freight analysis |

---

## ⚡ Quickstart Guide

### 1. Clone & Setup Environment

```bash
# Clone the repository
git clone https://github.com/your-username/semanticedge.git
cd semanticedge

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example configuration template
cp .env.example .env
```

### 3. Initialize Database & Seed Demo Data

```bash
# Run database migrations
python manage.py migrate

# Seed demo users, default camera, and documentation pages
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
| **Superuser / Admin** | `admin` | `admin123` |
| **Standard User** | `demo` | `demo123` |

---

## 📂 Project Structure

```
semanticedge/
├── manage.py                   # Django management utility
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── seed_demo.py                # Database initial seeding script
├── LICENSE                     # Apache 2.0 Open Source License
├── CONTRIBUTING.md             # Contributor guidelines & code standards
│
├── config/                     # Project configuration & settings
│   ├── settings.py             # Decouple configuration, auth, and static paths
│   ├── urls.py                 # Root URL router
│   ├── wsgi.py / asgi.py       # Production server gateways
│
├── src/                        # Core AI Inference & Tracking Package
│   ├── detector.py             # YOLOv8 detection wrapper
│   ├── tracker.py              # YOLOv8 + ByteTrack persistent tracker
│   ├── trajectory.py           # 30-point temporal trajectory store
│   ├── draw_utils.py           # Bounding box & label drawing utilities
│   ├── logger.py               # Structured CSV detection logger
│   └── main.py                 # Standalone OpenCV entrypoint
│
├── nvr/                        # NVR SaaS Product Application
│   ├── models.py               # Camera model with user ownership
│   ├── views.py                # Live, Review, Explore, Export, Settings views
│   ├── streaming.py            # MJPEG HTTP generator wrapping src/
│   ├── urls.py                 # NVR tab routes & telemetry APIs
│   └── tests.py                # Test suite for access control & endpoints
│
├── core/                       # Public Marketing Application
│   ├── views.py                # Landing page view
│   └── urls.py                 # Marketing routes
│
├── docs/                       # Model-Driven Documentation Application
│   ├── models.py               # DocPage model
│   ├── views.py                # Markdown to HTML compiler with Pygments
│   └── admin.py                # Admin Markdown editor
│
├── static/                     # Static assets
│   ├── css/design.css          # Ethereal Precision unified design system
│   └── js/main.js              # Telemetry pollers, modals & animations
│
└── templates/                  # Django HTML Templates
    ├── base.html               # Public marketing master shell
    ├── accounts/login.html     # Sign-in template
    ├── core/home.html          # Landing page template
    ├── docs/                   # Documentation templates
    └── nvr/                    # NVR Console Templates
        ├── base_nvr.html       # NVR master shell (Left rail + Status bar)
        ├── live.html           # Live camera feed viewport & telemetry
        ├── review.html         # Event review timeline & density bar
        ├── explore.html        # Category object discovery strips
        ├── export.html         # Evidence exporter
        ├── settings.html       # Camera & AI engine settings
        └── log.html            # CSV detection log viewer
```

---

## ⚙️ Hardware Acceleration

SemanticEdge supports flexible compute backends configurable via the `YOLO_DEVICE` variable in `.env`:

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

## 🔒 Security & Best Practices

- **RTSP Credentials**: Never commit RTSP connection strings with embedded passwords to git. Always use environment variable substitution.
- **Multi-Tenant Isolation**: Camera access is enforced at the view layer via `CameraOwnershipMixin`. Users cannot view video streams or telemetry from cameras they do not own.
- **Production Server**: For production environments, run behind Gunicorn / Uvicorn and NGINX with SSL termination.

---

## 🧪 Running Tests

SemanticEdge includes a comprehensive automated test suite testing routes, permissions, markdown rendering, and camera isolation:

```bash
# Run all test suites
python manage.py test core docs nvr

# Verbose test execution
python manage.py test core docs nvr -v 2
```

---

## 🤝 Contributing

Contributions are welcome! Please read our [CONTRIBUTING.md](CONTRIBUTING.md) guide for details on our code of conduct, branch conventions, and pull request workflow.

---

## 📄 License

This project is licensed under the **Apache License 2.0** - see the [LICENSE](LICENSE) file for details.
