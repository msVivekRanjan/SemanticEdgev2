"""
config/urls.py
--------------
Root URL configuration for SemanticEdge.

In SHOWCASE_MODE the /nvr/ prefix is excluded entirely so that nvr.urls
(and its transitive imports of OpenCV, YOLO, ByteTrack, RTSP helpers, etc.)
are never loaded at startup.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),
    # Public marketing / home
    path("", include("core.urls")),
    # Documentation (always public)
    path("docs/", include("docs.urls")),
    # Authentication (login / logout / register)
    path("accounts/", include("accounts.urls")),
]

# NVR product — only included when running in full local/NVR mode.
# In SHOWCASE_MODE this block is skipped so Edge-AI deps are never imported.
if not settings.SHOWCASE_MODE:
    urlpatterns += [
        path("nvr/", include("nvr.urls")),
    ]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

