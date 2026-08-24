"""
config/urls.py
--------------
Root URL configuration for SemanticEdge.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Django admin
    path("admin/", admin.site.urls),
    # Public marketing
    path("", include("core.urls")),
    # Documentation (public)
    path("docs/", include("docs.urls")),
    # Authentication
    path("accounts/", include("accounts.urls")),
    # NVR product (login required)
    path("nvr/", include("nvr.urls")),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
