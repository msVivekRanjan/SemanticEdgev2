"""docs/urls.py"""

from django.urls import path
from .views import DocsListView, DocDetailView

app_name = "docs"

urlpatterns = [
    path("", DocsListView.as_view(), name="list"),
    path("<slug:slug>/", DocDetailView.as_view(), name="detail"),
]
