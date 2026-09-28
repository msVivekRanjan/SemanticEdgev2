"""
nvr/urls.py
-----------
Routes for the professional NVR dashboard tabs, Edge AI services, and streaming APIs.
"""

from django.urls import path
from .views import (
    AssistantConversationApiView,
    AssistantConversationDetailApiView,
    AssistantDiagnosticsApiView,
    AssistantMessageApiView,
    CameraThresholdApiView,
    CameraZonesApiView,
    DeleteDetectionApiView,
    DetectionLogView,
    ExploreView,
    ExportCsvLogView,
    ExportView,
    LatestIntrusionsApiView,
    LiveView,
    ObjectCounterStreamView,
    ObjectCounterView,
    RawStreamView,
    RestrictedAreaView,
    ReviewView,
    SettingsView,
    StatsView,
    StreamView,
    SystemStatusApiView,
    UpdateDetectionDescriptionApiView,
)

app_name = "nvr"

urlpatterns = [
    # Primary tabs
    path("", LiveView.as_view(), name="dashboard"),
    path("dashboard/", LiveView.as_view(), name="dashboard_alias"),
    path("live/", LiveView.as_view(), name="live"),
    path("camera/<int:camera_id>/live/", LiveView.as_view(), name="camera_live"),

    # Edge AI Services Modules
    path("object-counter/", ObjectCounterView.as_view(), name="object_counter"),
    path("restricted-area/", RestrictedAreaView.as_view(), name="restricted_area"),

    # Other tabs
    path("review/", ReviewView.as_view(), name="review"),
    path("explore/", ExploreView.as_view(), name="explore"),
    path("export/", ExportView.as_view(), name="export"),
    path("export/csv/", ExportCsvLogView.as_view(), name="export_csv"),
    path("settings/", SettingsView.as_view(), name="settings"),

    # Video streaming & Telemetry
    path("camera/<int:camera_id>/stream/", StreamView.as_view(), name="stream"),
    path("camera/<int:camera_id>/raw-stream/", RawStreamView.as_view(), name="raw_stream"),
    path("camera/<int:camera_id>/counter-stream/", ObjectCounterStreamView.as_view(), name="counter_stream"),
    path("camera/<int:camera_id>/stats/", StatsView.as_view(), name="stats"),
    path("camera/<int:camera_id>/log/", DetectionLogView.as_view(), name="log"),
    path("logs/", DetectionLogView.as_view(), name="logs"),

    # Persistent status bar API & Real-time intrusion alerts
    path("api/system-status/", SystemStatusApiView.as_view(), name="system_status"),
    path("api/alerts/latest/", LatestIntrusionsApiView.as_view(), name="latest_alerts"),

    # Monitoring Zone & Calibration APIs
    path("api/camera/<int:camera_id>/zones/", CameraZonesApiView.as_view(), name="camera_zones"),
    path("api/camera/<int:camera_id>/night-threshold/", CameraThresholdApiView.as_view(), name="camera_night_threshold"),

    # Detection Event Action APIs
    path("api/detection/<int:event_id>/update-description/", UpdateDetectionDescriptionApiView.as_view(), name="api_update_description"),
    path("api/detection/<int:event_id>/delete/", DeleteDetectionApiView.as_view(), name="api_delete_detection"),

    # SemanticEdge Internal Assistant APIs
    path("api/assistant/conversations/", AssistantConversationApiView.as_view(), name="assistant_conversations"),
    path("api/assistant/conversations/<int:conversation_id>/", AssistantConversationDetailApiView.as_view(), name="assistant_conversation_detail"),
    path("api/assistant/conversations/<int:conversation_id>/messages/", AssistantMessageApiView.as_view(), name="assistant_messages"),
    path("api/assistant/diagnostics/", AssistantDiagnosticsApiView.as_view(), name="assistant_diagnostics"),
]

