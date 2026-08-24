# Contributing to SemanticEdge

Thank you for your interest in contributing to **SemanticEdge**! We welcome contributions from developers of all skill levels.

This guide outlines our development workflow, architectural invariants, coding standards, and pull request guidelines to help keep the codebase maintainable and production-ready.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Architectural Invariants](#architectural-invariants)
3. [Development Setup](#development-setup)
4. [Branching & Workflow](#branching--workflow)
5. [Coding Standards](#coding-standards)
6. [Testing & Quality Assurance](#testing--quality-assurance)
7. [Submitting a Pull Request](#submitting-a-pull-request)
8. [Reporting Issues](#reporting-issues)

---

## Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for everyone. Please treat all contributors with respect, constructiveness, and professional courtesy.

---

## Architectural Invariants

Before modifying code, please keep these core design principles in mind:

1. **Local-First & Privacy**: Video frames and inference data must never leave the local deployment network unless explicitly directed by an authorized export action.
2. **Detection Pipeline Encapsulation (`src/`)**:
   - `detector.py` and `tracker.py` share a uniform detection schema (`bbox`, `conf`, `cls_id`, `cls_name`, `track_id`).
   - `logger.py` exposes a minimal contract (`init_logger()`, `log_entry()`) so backends can be swapped without touching caller logic.
   - Streaming is decoupled via a generator (`nvr/streaming.py`) producing standard `multipart/x-mixed-replace` JPEG streams.
3. **Multi-Tenant Isolation**: Every camera view and telemetry endpoint must enforce ownership checks against `request.user`.
4. **Environment-Driven Configuration**: No secrets (RTSP credentials, database passwords, secret keys) may ever be committed or hardcoded. Always use `python-decouple`.

---

## Development Setup

### 1. Prerequisites
- Python 3.10+ (tested on Python 3.10, 3.11, 3.12, 3.14)
- Git
- A working webcam, video file, or accessible RTSP test stream

### 2. Setup Virtual Environment

```bash
# Clone your fork
git clone https://github.com/<your-username>/semanticedge.git
cd semanticedge

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Create local environment configuration
cp .env.example .env

# Run database migrations
python manage.py migrate

# Seed initial users (admin/admin123, demo/demo123) and sample documentation
python seed_demo.py
```

### 4. Run Development Server

```bash
python manage.py runserver 127.0.0.1:8000
```

Visit `http://127.0.0.1:8000/` to view the landing page, or log in to the NVR console at `http://127.0.0.1:8000/accounts/login/`.

---

## Branching & Workflow

We follow standard GitHub Flow:

1. **Fork** the repository.
2. Create a topic branch from `main`:
   - `feature/add-rtsp-health-check` (new features)
   - `fix/macos-avfoundation-index` (bug fixes)
   - `docs/add-jetson-setup-guide` (documentation)
   - `refactor/clean-stats-lock` (refactoring)
3. Keep commits atomic and write clear, descriptive commit messages:
   ```
   feat(nvr): add multi-grid 2x2 camera display
   fix(streaming): resolve memory leak on client disconnection
   docs(readme): add cuda 12.x setup instructions
   ```

---

## Coding Standards

### Python Backend
- **PEP 8 Compliance**: Use 4 spaces per indentation level. Maximum line length 100-120 characters where reasonable.
- **Type Annotations**: Provide type hints for function signatures and public APIs.
- **Docstrings**: Document classes, helper functions, and views using Google or NumPy docstring format.
- **Django Conventions**:
  - Prefer Class-Based Views (`TemplateView`, `ListView`, `DetailView`) with `LoginRequiredMixin`.
  - Avoid heavy business logic in template context processors or templates.
  - Wrap database operations in `select_related` / `prefetch_related` where foreign keys are traversed.

### Frontend (CSS & JS)
- **Vanilla CSS Tokens**: Utilize CSS custom properties defined in `static/css/design.css` (`--surface`, `--primary`, `--font-sans`, etc.). Avoid inventing ad-hoc hex codes.
- **Vanilla JS**: Keep clientside scripts modular, performant, and dependency-free. Always clean up intervals on `pagehide` or disconnect.

---

## Testing & Quality Assurance

All pull requests must pass the automated test suite before merging:

```bash
# Run all test suites
python manage.py test core docs nvr

# Run tests with verbose output
python manage.py test core docs nvr -v 2
```

### Writing Tests
- Any new view or endpoint must include automated test cases in the respective app's `tests.py`.
- Always test both authenticated access (200 OK) and unauthorized / non-owner access (302 redirect or 403 Forbidden).

---

## Submitting a Pull Request

Before opening a pull request, ensure:

1. [ ] Code adheres to PEP 8 and project style conventions.
2. [ ] All tests pass (`python manage.py test`).
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
