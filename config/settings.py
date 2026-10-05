"""
config/settings.py
------------------
SemanticEdge Django configuration.
All secrets are loaded from environment variables via python-decouple.
Never hardcode SECRET_KEY, DB credentials, or camera RTSP URLs.
"""

import os
from pathlib import Path
from decouple import config, Csv

# ── Paths ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# The SemanticEdgev2 repo root (one level above semanticedge/)
REPO_ROOT = BASE_DIR.parent

# ── Security ─────────────────────────────────────────────────────────────────
SECRET_KEY = config("SECRET_KEY", default="dev-insecure-key-replace-in-production")
DEBUG = config("DEBUG", default=True, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

# Automatically add the Render hostname
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])

# ── Showcase Mode ────────────────────────────────────────────────────────────
# When SHOWCASE_MODE=true (e.g. on Render), the nvr app is NOT loaded.
# This prevents OpenCV, YOLO, ByteTrack, RTSP, and all Edge-AI dependencies
# from being imported at startup. Home, Docs, Accounts/Login, and Support
# remain fully functional. Set SHOWCASE_MODE=false for full local NVR mode.
SHOWCASE_MODE = config("SHOWCASE_MODE", default=False, cast=bool)

# ── Application definition ───────────────────────────────────────────────────
_base_apps = [
    # Django built-ins
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # SemanticEdge apps (always loaded)
    "core",
    "docs",
    "accounts",
]

INSTALLED_APPS = _base_apps if SHOWCASE_MODE else _base_apps + ["nvr"]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Project-level templates/ directory
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ── Database ─────────────────────────────────────────────────────────────────
# Default: SQLite (development). Override DATABASE_URL for production.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ── Auth ─────────────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Login/logout redirect targets
LOGIN_URL = "/accounts/login/"
# In Showcase Mode, redirect to home after login (no NVR to go to).
# In full local mode, redirect to the NVR dashboard.
LOGIN_REDIRECT_URL = "/" if SHOWCASE_MODE else "/nvr/dashboard/"
LOGOUT_REDIRECT_URL = "/"

# ── Internationalisation ─────────────────────────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static files ─────────────────────────────────────────────────────────────
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"
)

# ── Media (uploads) ──────────────────────────────────────────────────────────
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ── Detection pipeline settings ──────────────────────────────────────────────
# Loaded by nvr/streaming.py — never hardcoded
YOLO_MODEL_PATH = config("YOLO_MODEL_PATH", default=str(BASE_DIR / "yolov8n.pt"))
YOLO_CONF_THRESHOLD = config("YOLO_CONF_THRESHOLD", default=0.40, cast=float)
YOLO_DEVICE = config("YOLO_DEVICE", default="cpu")

# (Telegram / OpenClaw integration has been removed from SemanticEdge v2)

# ── Misc ─────────────────────────────────────────────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
