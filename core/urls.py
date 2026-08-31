"""core/urls.py"""

from django.urls import path
from .views import HomeView, BookDemoView

app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("book-demo/", BookDemoView.as_view(), name="book_demo"),
    path("demo/", BookDemoView.as_view(), name="demo_alias"),
]
