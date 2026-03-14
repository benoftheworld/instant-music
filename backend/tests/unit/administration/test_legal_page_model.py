"""Tests unitaires du modèle LegalPage."""

from unittest.mock import MagicMock

from django.db import models

from apps.administration.models import LegalPage
from tests.base import BaseModelUnitTest


class TestLegalPageModel(BaseModelUnitTest):
    """Vérifie les champs et métadonnées du modèle LegalPage."""

    def get_model_class(self):
        return LegalPage

    # ── page_type ───────────────────────────────────────────────────

    def test_page_type_max_length(self):
        self.assert_field_max_length(LegalPage, "page_type", 20)

    def test_page_type_choices(self):
        self.assert_field_choices(LegalPage, "page_type", LegalPage.PageType.choices)

    def test_page_type_unique(self):
        self.assert_field_unique(LegalPage, "page_type", True)

    def test_page_type_values(self):
        assert LegalPage.PageType.PRIVACY == "privacy"
        assert LegalPage.PageType.LEGAL == "legal"

    # ── Champs textes ───────────────────────────────────────────────

    def test_title_max_length(self):
        self.assert_field_max_length(LegalPage, "title", 200)

    def test_content_is_textfield(self):
        self.assert_field_type(LegalPage, "content", models.TextField)

    # ── updated_at ──────────────────────────────────────────────────

    def test_updated_at_auto_now(self):
        field = LegalPage._meta.get_field("updated_at")
        assert field.auto_now is True

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("Page légale", "Pages légales")

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        """__str__ appelle get_page_type_display()."""
        page = MagicMock(spec=LegalPage)
        page.get_page_type_display.return_value = "Mentions légales"
        result = LegalPage.__str__(page)
        assert result == "Mentions légales"
