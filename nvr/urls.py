"""
nvr/urls.py
-----------
Routes for the professional NVR dashboard tabs, Edge AI services, and streaming APIs.
"""

from django.urls import path
from .views import (
    DetectionLogView,
    ExploreView,
    ExportView,
    FaceRecognitionView,
    FaceStreamView,
    LiveView,
    ObjectCounterStreamView,
    ObjectCounterView,
    RawStreamView,
    ReviewView,
    SettingsView,
    StatsView,
    StreamView,
    SystemStatusApiView,
)

app_name = "nvr"

urlpatterns = [
    # Primary tabs
    path("", LiveView.as_view(), name="dashboard"),
    path("dashboard/", LiveView.as_view(), name="dashboard_alias"),
    path("live/", LiveView.as_view(), name="live"),
    path("camera/<int:camera_id>/live/", LiveView.as_view(), name="camera_live"),

    # Edge AI Services Modules
    path("face-recognition/", FaceRecognitionView.as_view(), name="face_recognition"),
    path("object-counter/", ObjectCounterView.as_view(), name="object_counter"),

    # Other tabs
    path("review/", ReviewView.as_view(), name="review"),
    path("explore/", ExploreView.as_view(), name="explore"),
    path("export/", ExportView.as_view(), name="export"),
    path("settings/", SettingsView.as_view(), name="settings"),

    # Video streaming & Telemetry
    path("camera/<int:camera_id>/stream/", StreamView.as_view(), name="stream"),
    path("camera/<int:camera_id>/raw-stream/", RawStreamView.as_view(), name="raw_stream"),
    path("camera/<int:camera_id>/face-stream/", FaceStreamView.as_view(), name="face_stream"),
    path("camera/<int:camera_id>/counter-stream/", ObjectCounterStreamView.as_view(), name="counter_stream"),
    path("camera/<int:camera_id>/stats/", StatsView.as_view(), name="stats"),
    path("camera/<int:camera_id>/log/", DetectionLogView.as_view(), name="log"),

    # Persistent status bar API
    path("api/system-status/", SystemStatusApiView.as_view(), name="system_status"),
]
