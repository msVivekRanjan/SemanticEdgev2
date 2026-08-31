"""docs/tests.py"""

from django.test import TestCase
from django.urls import reverse
from .models import DocPage


class DocsViewTests(TestCase):
    def setUp(self):
        self.page = DocPage.objects.create(
            title="Test Doc",
            slug="test-doc",
            category="General",
            order=1,
            content_markdown="# Heading 1\n\nThis is a **test** doc with `code`.",
        )

    def test_docs_list_redirects_to_first_page(self):
        response = self.client.get(reverse("docs:list"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.page.get_absolute_url())

    def test_doc_detail_view_and_markdown_rendering(self):
        response = self.client.get(reverse("docs:detail", kwargs={"slug": "test-doc"}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "docs/detail.html")
        self.assertContains(response, "Heading 1</h1>")
        self.assertContains(response, "<strong>test</strong>")
        self.assertContains(response, "<code>code</code>")
        self.assertContains(response, "Download .MD")
        self.assertContains(response, "On This Page")

    def test_doc_detail_toc_and_prev_next_navigation(self):
        page2 = DocPage.objects.create(
            title="Second Doc",
            slug="second-doc",
            category="General",
            order=2,
            content_markdown="## Architecture Overview\n\nSome text.\n\n### Pipeline Details\n\nMore text.",
        )
        response = self.client.get(reverse("docs:detail", kwargs={"slug": "second-doc"}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Architecture Overview")
        self.assertContains(response, "Pipeline Details")
        self.assertContains(response, "Previous Document")
        self.assertContains(response, "Test Doc")

    def test_doc_markdown_download(self):
        response = self.client.get(reverse("docs:download_markdown", kwargs={"slug": "test-doc"}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/markdown; charset=utf-8")
        self.assertIn("attachment; filename=\"test-doc.md\"", response["Content-Disposition"])
        self.assertIn("# Heading 1", response.content.decode("utf-8"))

