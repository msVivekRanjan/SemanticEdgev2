# Contributing to SemanticEdge

Thank you for your interest in contributing to **SemanticEdge**! We welcome contributions from developers, security researchers, and computer vision engineers of all skill levels.

This guide outlines our development workflow, architectural invariants, coding standards, and pull request guidelines to keep the codebase maintainable, performant, and production-grade.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Architectural Invariants](#architectural-invariants)
3. [Development Setup](#development-setup)
4. [Branching & Workflow](#branching--workflow)
5. [Coding Standards](#coding-standards)
6. [Testing & Quality Assurance](#testing--quality-assurance)
7. [Documentation Contributions](#documentation-contributions)
8. [Submitting a Pull Request](#submitting-a-pull-request)
9. [Reporting Issues](#reporting-issues)

---

## Code of Conduct

We are committed to providing an open, friendly, and harassment-free environment for all contributors. Please treat fellow developers with respect, empathy, and professional courtesy at all times.

---

## Architectural Invariants

Before writing or modifying code, ensure your changes respect these core system design principles:

### 1. Local-First & Privacy Architecture
- Video frames, inference tensors, biometric profiles, and detection telemetry must never leave the local deployment perimeter unless an authorized user explicitly initiates an export or alert.

### 2. Detection Pipeline Encapsulation (`src/`)
- `detector.py` and `tracker.py` share a strict detection schema: `(bbox, conf, cls_id, cls_name, track_id)`.
- `logger.py` exposes a decoupled interface (`init_logger()`, `log_entry()`) so telemetry backends can be swapped without touching caller logic.
- Streaming is decoupled via generators (`nvr/streaming.py`) producing standard `multipart/x-mixed-replace` JPEG streams.

### 3. Multi-Tenant Isolation & Camera Ownership
- Every camera view, feed, and telemetry endpoint must enforce ownership checks against `request.user` (or grant access if user is `is_staff` / `is_superuser`).
- Users must never access or modify streams, zones, or event records belonging to another tenant.

### 4. Camera Soft-Delete & Detection History Preservation
- When a user deletes a camera, the system toggles `is_active=False` rather than performing a database `DELETE CASCADE`.
- If a camera with the same source URL is re-registered by the user, the existing `Camera` record is reactivated (`is_active=True`), preserving all historical detections, snapshots, and track IDs.

### 5. Perimeter Monitoring Zone Geometry
- All monitoring zone coordinates must be stored as normalized float points `[[x, y], ...]` with values between `0.0` and `1.0`.
- This ensures zone boundaries scale correctly across disparate capture resolutions (4K, 1080p, 720p).

### 6. Telegram Security Assistant Standards
- **Backend NLP Only**: OpenClaw acts strictly as an intent parser. It must never directly access low-level camera drivers or send unformatted raw data.
- **Strict Authentication**: Any user communicating with the bot must authenticate against Django's `auth_user` table before surveillance data or snapshots are delivered.
- **Single Poller Consumer**: Only `python manage.py run_openclaw_bot` may consume Telegram updates. Never spawn multiple polling processes on the same bot token.
- **Zero-Emoji CCTV Format**: Surveillance reports, alert notifications, captions, and system status messages must use clean ASCII divider lines (`----------------------------------------`) and uppercase headers. Emojis are strictly disallowed in surveillance reports.
- **User Feedback Loop**: Every completed operational query prompts for user feedback (`YES`/`NO`), recorded into the `TelegramFeedback` database model.

### 7. Browser-Compatible Video Encoding
- All exported video clips must be encoded in **H.264 / AVC1** container format (with automatic FFmpeg transcode fallback) to ensure seamless playback in HTML5 `<video>` players without requiring desktop codecs.

---

## Development Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.10, 3.11, 3.12, 3.14)
- Git
- A working webcam, video file, or reachable RTSP test stream

### 2. Setup Virtual Environment

```bash
# Clone your fork
git clone https://github.com/<your-username>/semanticedge.git
cd semanticedge

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Option A: Full Edge AI Environment (YOLOv8, PyTorch, OpenCV)
pip install -r requirements.txt

# Option B: Lightweight Web / PaaS Environment (Web UI & Docs only)
pip install -r requirements-render.txt
```

### 3. Environment Configuration

```bash
# Create local environment configuration
cp .env.example .env

# Run database migrations
python manage.py migrate

# Seed initial users, default camera, and 9 documentation pages
python seed_demo.py
```

### 4. Run Development Services

```bash
# Terminal 1: Run Web & NVR Application
python manage.py runserver 127.0.0.1:8000

# Terminal 2 (Optional): Run Telegram Security Assistant Poller
python manage.py run_openclaw_bot
```

Visit `http://127.0.0.1:8000/` to view the landing page, or log in to the NVR console at `http://127.0.0.1:8000/accounts/login/`.

---

## Branching & Workflow

We follow standard GitHub Flow:

1. **Fork** the repository.
2. Create a topic branch from `main`:
   - `feat/telegram-nlp-expansion` (new features)
   - `fix/h264-transcode-fallback` (bug fixes)
   - `docs/add-monitoring-zones-guide` (documentation)
   - `refactor/openclaw-state-machine` (refactoring)
3. Keep commits atomic and write conventional commit messages:
   ```
   feat(nvr): add polygon restricted zone evaluation
   fix(openclaw): handle markdown escaping in alerts
   docs(readme): update quickstart and architecture
   ```

---

## Coding Standards

### Python Backend
- **PEP 8 Compliance**: Use 4 spaces per indentation level. Maximum line length 100-120 characters where practical.
- **Type Annotations**: Provide type hints for function signatures and public APIs.
- **Docstrings**: Document classes, helper functions, and views using Google or NumPy docstring format.
- **Django Conventions**:
  - Prefer Class-Based Views (`TemplateView`, `ListView`, `DetailView`) with `LoginRequiredMixin`.
  - Avoid heavy business logic in template context processors or templates.
  - Wrap database operations in `select_related` / `prefetch_related` where foreign keys are traversed.

### Frontend (CSS & JS)
- **Vanilla CSS Tokens**: Utilize CSS custom properties defined in `static/css/design.css` (`--surface-base`, `--primary`, `--font-sans`, etc.). Avoid hardcoded hex colors.
- **Vanilla JS**: Keep clientside scripts modular, performant, and dependency-free. Always clean up intervals on `pagehide` or disconnect.

---

## Testing & Quality Assurance

All pull requests must pass the automated test suite before merging:

```bash
# Run all test suites across all apps
python manage.py test accounts core docs nvr

# Run tests with verbose output
python manage.py test accounts core docs nvr -v 2
```

### Writing Tests
- Any new view, endpoint, model, or NLP intent must include automated test cases in the respective app's `tests.py`.
- Always test both authenticated access (200 OK) and unauthorized / non-owner access (302 redirect or 403 Forbidden).
- For Telegram features, test the authentication state machine, unauthenticated denial, query execution, feedback collection, and zero-emoji assertion.

---

## Documentation Contributions

Documentation pages are model-driven (`DocPage` in `docs/models.py`) and rendered dynamically at `/docs/<slug>/`:

1. When adding or updating documentation, update the entries in `seed_demo.py` so new installations receive the docs.
2. DocPages support standard Markdown, GitHub-style alerts (`> [!NOTE]`, `> [!WARNING]`), tables, and code syntax highlighting via Pygments.
3. Verify that new documentation pages have a unique `slug`, appropriate `category`, and an `order` integer for sidebar sorting.

---

## Submitting a Pull Request

Before opening a pull request, verify:

1. [ ] Code adheres to PEP 8 and project style conventions.
2. [ ] All 36+ tests pass (`python manage.py test accounts core docs nvr`).
3. [ ] System check passes cleanly (`python manage.py check`).
4. [ ] No sensitive credentials, `.env` files, or binary logs are committed.
5. [ ] Relevant documentation or docstrings have been updated.

When submitting:
- Provide a clear title and description explaining *what* was changed and *why*.
- Include before/after screenshots or terminal logs for visual UI or pipeline changes.

---

## Reporting Issues

If you find a bug or have a feature proposal:
1. Check existing [GitHub Issues](https://github.com/your-org/semanticedge/issues) to avoid duplicates.
2. Open a new issue with:
   - Clear description and steps to reproduce.
   - Operating System, Python version, PyTorch / CUDA version, and OpenCV version.
   - Relevant terminal output or traceback logs.

Thank you for helping make SemanticEdge the leading open-source Edge AI NVR!
