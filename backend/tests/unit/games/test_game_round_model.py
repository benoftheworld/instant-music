"""Tests unitaires du modèle GameRound — introspection des champs."""

from unittest.mock import MagicMock

from apps.games.models import GameRound
from tests.base import BaseModelUnitTest


class TestGameRoundModel(BaseModelUnitTest):
    """Vérifie les champs, contraintes et métadonnées du modèle GameRound."""

    def get_model_class(self):
        return GameRound

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champs texte ────────────────────────────────────────────────

    def test_track_id_max_length(self):
        self.assert_field_max_length(GameRound, "track_id", 255)

    def test_track_name_max_length(self):
        self.assert_field_max_length(GameRound, "track_name", 255)

    def test_artist_name_max_length(self):
        self.assert_field_max_length(GameRound, "artist_name", 255)

    def test_correct_answer_max_length(self):
        self.assert_field_max_length(GameRound, "correct_answer", 255)

    def test_question_type_max_length(self):
        self.assert_field_max_length(GameRound, "question_type", 30)

    def test_question_text_max_length(self):
        self.assert_field_max_length(GameRound, "question_text", 500)

    # ── Valeurs par défaut ──────────────────────────────────────────

    def test_question_type_default(self):
        self.assert_field_default(GameRound, "question_type", "guess_title")

    def test_question_text_default(self):
        self.assert_field_default(
            GameRound, "question_text", "Quel est le titre de ce morceau ?"
        )

    def test_options_default(self):
        self.assert_field_default(GameRound, "options", list)

    def test_extra_data_default(self):
        self.assert_field_default(GameRound, "extra_data", dict)

    def test_duration_default(self):
        self.assert_field_default(GameRound, "duration", 30)

    def test_preview_url_blank(self):
        self.assert_field_blank(GameRound, "preview_url", True)

    def test_preview_url_max_length(self):
        self.assert_field_max_length(GameRound, "preview_url", 500)

    # ── Timestamps ──────────────────────────────────────────────────

    def test_started_at_null(self):
        self.assert_field_null(GameRound, "started_at", True)

    def test_ended_at_null(self):
        self.assert_field_null(GameRound, "ended_at", True)

    # ── ForeignKey ──────────────────────────────────────────────────

    def test_game_field_exists(self):
        self.assert_field_exists(GameRound, "game")

    def test_game_cascade(self):
        field = GameRound._meta.get_field("game")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("round", "rounds")

    def test_unique_together(self):
        self.assert_unique_together(GameRound, ["game", "round_number"])

    def test_ordering(self):
        self.assert_ordering(GameRound, ["game", "round_number"])

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        mock_game = MagicMock()
        mock_game.room_code = "AAA111"
        round_obj = MagicMock(spec=GameRound)
        round_obj.round_number = 3
        round_obj.game = mock_game
        result = GameRound.__str__(round_obj)
        assert "3" in result
        assert "AAA111" in result
