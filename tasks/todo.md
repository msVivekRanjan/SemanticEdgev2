# Task: Update README, Contributing.md, and Documentation System

- [x] 1. Update `README.md` with Recent Capabilities <!-- id: 0 -->
  - [x] Add Telegram Security Assistant & OpenClaw NLP section (authentication, surveillance commands, feedback loop, poller daemon).
  - [x] Add Perimeter Monitoring Zones & Tripwire Intrusion Alerting section.
  - [x] Add Face Recognition Attendance & Industrial Object Counting features.
  - [x] Add Evidence Exporting with H.264 / AVC1 web-ready transcoding & CSV exports.
  - [x] Add Cloud & Lightweight Deployment section referencing `requirements-render.txt`.
  - [x] Update testing commands to include `accounts`, `core`, `docs`, `nvr` (36 tests).
  - [x] Update directory structure to show OpenClaw, Telegram session models, and new templates.

- [x] 2. Update `CONTRIBUTING.md` <!-- id: 1 -->
  - [x] Update architectural invariants (Telegram Security Assistant, CCTV zero-emoji standard, zone geometry, camera soft-delete reuse).
  - [x] Update development dependencies and test commands (`python manage.py test accounts core docs nvr`).
  - [x] Add guidelines for adding new DocPages, NLP intents, and edge AI services.

- [x] 3. Update Existing Documentation Pages in `docs/` and `seed_demo.py` <!-- id: 2 -->
  - [x] Update `getting-started`: include all NVR tabs, Telegram bot daemon, credentials, and startup flow.
  - [x] Update `supported-classes`: document standard 6 COCO classes, face references, and custom zone class filtering.
  - [x] Update `camera-configuration`: document RTSP, camera soft-delete reuse, day/night thresholding, and multi-camera grid.

- [x] 4. Create New Documentation Pages for `docs/` App & Seed to Database <!-- id: 3 -->
  - [x] `telegram-security-assistant`: Bot setup, authentication flow, NLP query syntax, feedback system, daemon runner.
  - [x] `monitoring-zones-intrusion`: Polygon restricted zones, tripwire line crossing, coordinate normalization, instant alerts.
  - [x] `face-recognition-attendance`: FaceReference profile enrollment, live matching, attendance audit logs.
  - [x] `object-counter-industrial`: Bidirectional line counting, conveyor item counting, rate-per-minute metrics.
  - [x] `evidence-export-transcoding`: Video clipping, H.264/AVC1 browser transcoding, snapshot archive, CSV export.
  - [x] `lightweight-cloud-deployment`: Render/PaaS hosting using `requirements-render.txt`, WhiteNoise, Gunicorn.
  - [x] Update `seed_demo.py` with the complete documentation catalogue and execute database update.

- [x] 5. Testing & Verification <!-- id: 4 -->
  - [x] Run full test suite (`python manage.py test accounts core docs nvr`) to ensure all 36+ tests pass cleanly.
  - [x] Verify docs list and detail views render correctly with syntax highlighting, TOC, and navigation.

## Review & Verification Summary

1. **`README.md` Overhaul**:
   - Added Telegram Security Assistant & OpenClaw section with authentication flow, surveillance query syntax, and feedback loop.
   - Added Perimeter Monitoring Zones & Intrusion Detection section.
   - Added Face Recognition Attendance & Industrial Object Counter sections.
   - Added Evidence Exporter with browser-compatible H.264 / AVC1 transcoding and CSV export.
   - Added Cloud & Lightweight Deployment section referencing `requirements-render.txt` with Render build/start commands.
   - Updated test commands to `python manage.py test accounts core docs nvr` (36 tests passing).
   - Updated directory tree with all models, templates, and management commands.

2. **`CONTRIBUTING.md` Overhaul**:
   - Added architectural invariants for Telegram integration (backend NLP only, auth validation, zero emojis, feedback logging).
   - Added invariants for normalized zone coordinates (`0.0 - 1.0`) and camera soft-delete reuse.
   - Added DocPage authoring standards and guidelines for edge AI modules.
   - Updated setup steps to include both full edge AI (`requirements.txt`) and lightweight web (`requirements-render.txt`).

3. **Documentation Catalogue (9 Pages in SQLite & `seed_demo.py`)**:
   - `getting-started`: Quick Start guide with all 8 navigation tabs, daemon runner, and credentials.
   - `supported-classes`: 6 COCO security classes + Face Reference biometric profile.
   - `camera-configuration`: RTSP sources, soft-delete reuse, day/night thresholding, focus vs grid.
   - `telegram-security-assistant`: Bot token configuration, auth state machine, operational NLP queries, feedback loop.
   - `monitoring-zones-intrusion`: Polygon restricted zones, tripwires, coordinate normalization, automated alert trigger.
   - `face-recognition-attendance`: Reference profile enrollment, matching pipeline, attendance records.
   - `object-counter-industrial`: Bidirectional line counting, conveyor throughput, rate-per-minute metrics.
   - `evidence-export-transcoding`: Video clipping, H.264/AVC1 encoding, FastStart atom, CSV logs.
   - `lightweight-cloud-deployment`: Render/PaaS deployment with `requirements-render.txt`, WhiteNoise, Gunicorn.

4. **Testing Status**:
   - `python manage.py test accounts core docs nvr`: 36/36 tests passed in 8.925s.
