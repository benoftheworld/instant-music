"""Tests unitaires du modèle Achievement."""

from unittest.mock import MagicMock

from django.db import models

from apps.achievements.models import Achievement
from tests.base import BaseModelUnitTest


class TestAchievementModel(BaseModelUnitTest):
    """Vérifie les champs et métadonnées du modèle Achievement."""

    def get_model_class(self):
        return Achievement

    # ── PK ──────────────────────────────────────────────────────────

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champs textes ───────────────────────────────────────────────

    def test_name_max_length(self):
        self.assert_field_max_length(Achievement, "name", 100)

    def test_description_is_textfield(self):
        self.assert_field_type(Achievement, "description", models.TextField)

    # ── icon ────────────────────────────────────────────────────────

    def test_icon_null(self):
        self.assert_field_null(Achievement, "icon", True)

    def test_icon_blank(self):
        self.assert_field_blank(Achievement, "icon", True)

    # ── points ──────────────────────────────────────────────────────

    def test_points_default(self):
        self.assert_field_default(Achievement, "points", 10)

    # ── Conditions ──────────────────────────────────────────────────

    def test_condition_type_max_length(self):
        self.assert_field_max_length(Achievement, "condition_type", 50)

    def test_condition_value_is_integer(self):
        self.assert_field_type(Achievement, "condition_value", models.IntegerField)

    def test_condition_extra_max_length(self):
        self.assert_field_max_length(Achievement, "condition_extra", 100)

    def test_condition_extra_null(self):
        self.assert_field_null(Achievement, "condition_extra", True)

    def test_condition_extra_blank(self):
        self.assert_field_blank(Achievement, "condition_extra", True)

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("succès", "succès")

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        achievement = MagicMock(spec=Achievement)
        achievement.name = "Premier pas"
        result = Achievement.__str__(achievement)
        assert result == "Premier pas"
