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
