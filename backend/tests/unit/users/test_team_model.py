"""Tests unitaires du modèle Team — introspection des champs."""

from unittest.mock import MagicMock

from django.db import models

from apps.users.models import Team
from tests.base import BaseModelUnitTest


class TestTeamModel(BaseModelUnitTest):
    """Vérifie les champs, contraintes et métadonnées du modèle Team."""

    def get_model_class(self):
        return Team

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champ name ──────────────────────────────────────────────────

    def test_name_max_length(self):
        self.assert_field_max_length(Team, "name", 100)

    def test_name_unique(self):
        self.assert_field_unique(Team, "name", True)

    # ── Champ description ───────────────────────────────────────────

    def test_description_max_length(self):
        self.assert_field_max_length(Team, "description", 500)

    def test_description_blank(self):
        self.assert_field_blank(Team, "description", True)

    # ── Champ avatar ────────────────────────────────────────────────

    def test_avatar_null(self):
        self.assert_field_null(Team, "avatar", True)

    def test_avatar_blank(self):
        self.assert_field_blank(Team, "avatar", True)

    # ── Stats ───────────────────────────────────────────────────────

    def test_total_games_default(self):
        self.assert_field_default(Team, "total_games", 0)

    def test_total_wins_default(self):
        self.assert_field_default(Team, "total_wins", 0)

    def test_total_points_default(self):
        self.assert_field_default(Team, "total_points", 0)

    # ── ForeignKey owner ────────────────────────────────────────────

    def test_owner_field_exists(self):
        self.assert_field_exists(Team, "owner")

    def test_owner_cascade(self):
        field = Team._meta.get_field("owner")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("équipe", "équipes")

    def test_ordering(self):
        self.assert_ordering(Team, ["-total_points"])

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_returns_name(self):
        team = MagicMock(spec=Team)
        team.name = "Les Champions"
        assert Team.__str__(team) == "Les Champions"
