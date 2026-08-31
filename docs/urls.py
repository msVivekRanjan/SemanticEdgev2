"""
docs/urls.py
------------
URL routing for documentation pages and markdown exports.
"""

from django.urls import path
from .views import DocDetailView, DocMarkdownDownloadView, DocsListView

app_name = "docs"

urlpatterns = [
    path("", DocsListView.as_view(), name="list"),
    path("<slug:slug>/", DocDetailView.as_view(), name="detail"),
    path("<slug:slug>/download/", DocMarkdownDownloadView.as_view(), name="download_markdown"),
]
