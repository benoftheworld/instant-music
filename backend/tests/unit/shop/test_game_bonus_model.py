"""Tests unitaires du modèle GameBonus."""

from unittest.mock import MagicMock

from apps.shop.models import BonusType, GameBonus
from tests.base import BaseModelUnitTest


class TestGameBonusModel(BaseModelUnitTest):
    """Vérifie les champs et métadonnées du modèle GameBonus."""

    def get_model_class(self):
        return GameBonus

    # ── PK ──────────────────────────────────────────────────────────

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── bonus_type ──────────────────────────────────────────────────

    def test_bonus_type_max_length(self):
        self.assert_field_max_length(GameBonus, "bonus_type", 30)

    def test_bonus_type_choices(self):
        self.assert_field_choices(GameBonus, "bonus_type", BonusType.choices)

    def test_bonus_type_db_index(self):
        self.assert_field_db_index(GameBonus, "bonus_type", True)

    # ── round_number ────────────────────────────────────────────────

    def test_round_number_null(self):
        self.assert_field_null(GameBonus, "round_number", True)

    def test_round_number_blank(self):
        self.assert_field_blank(GameBonus, "round_number", True)

    def test_round_number_db_index(self):
        self.assert_field_db_index(GameBonus, "round_number", True)

    # ── is_used / timestamps ────────────────────────────────────────

    def test_is_used_default(self):
        self.assert_field_default(GameBonus, "is_used", False)

    def test_is_used_db_index(self):
        self.assert_field_db_index(GameBonus, "is_used", True)

    def test_used_at_null(self):
        self.assert_field_null(GameBonus, "used_at", True)

    def test_activated_at_auto_now_add(self):
        field = GameBonus._meta.get_field("activated_at")
        assert field.auto_now_add is True

    # ── FK ──────────────────────────────────────────────────────────

    def test_game_cascade(self):
        field = GameBonus._meta.get_field("game")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    def test_player_cascade(self):
        field = GameBonus._meta.get_field("player")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("bonus en partie", "bonus en partie")

    def test_ordering(self):
        self.assert_ordering(GameBonus, ["-activated_at"])

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        mock_user = MagicMock()
        mock_user.username = "bob"
        mock_player = MagicMock()
        mock_player.user = mock_user
        bonus = MagicMock(spec=GameBonus)
        bonus.player = mock_player
        bonus.bonus_type = "fog"
        bonus.round_number = 3
        result = GameBonus.__str__(bonus)
        assert "bob" in result
        assert "fog" in result
