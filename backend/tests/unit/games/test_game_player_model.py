"""Tests unitaires du modèle GamePlayer — introspection des champs."""

from unittest.mock import MagicMock

from apps.games.models import GamePlayer
from tests.base import BaseModelUnitTest


class TestGamePlayerModel(BaseModelUnitTest):
    """Vérifie les champs, contraintes et métadonnées du modèle GamePlayer."""

    def get_model_class(self):
        return GamePlayer

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champs ──────────────────────────────────────────────────────

    def test_score_default(self):
        self.assert_field_default(GamePlayer, "score", 0)

    def test_score_db_index(self):
        self.assert_field_db_index(GamePlayer, "score", True)

    def test_rank_null(self):
        self.assert_field_null(GamePlayer, "rank", True)

    def test_rank_blank(self):
        self.assert_field_blank(GamePlayer, "rank", True)

    def test_consecutive_correct_default(self):
        self.assert_field_default(GamePlayer, "consecutive_correct", 0)

    def test_is_connected_default(self):
        self.assert_field_default(GamePlayer, "is_connected", True)

    def test_is_connected_db_index(self):
        self.assert_field_db_index(GamePlayer, "is_connected", True)

    # ── Timestamps ──────────────────────────────────────────────────

    def test_joined_at_auto_now_add(self):
        field = GamePlayer._meta.get_field("joined_at")
        assert field.auto_now_add is True

    # ── ForeignKeys ─────────────────────────────────────────────────

    def test_game_cascade(self):
        field = GamePlayer._meta.get_field("game")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    def test_user_cascade(self):
        field = GamePlayer._meta.get_field("user")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("joueur de partie", "joueurs de partie")

    def test_unique_together(self):
        self.assert_unique_together(GamePlayer, ["game", "user"])

    def test_ordering(self):
        self.assert_ordering(GamePlayer, ["-score"])

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        mock_user = MagicMock()
        mock_user.username = "player1"
        mock_game = MagicMock()
        mock_game.room_code = "XYZ789"
        player = MagicMock(spec=GamePlayer)
        player.user = mock_user
        player.game = mock_game
        result = GamePlayer.__str__(player)
        assert "player1" in result
        assert "XYZ789" in result
