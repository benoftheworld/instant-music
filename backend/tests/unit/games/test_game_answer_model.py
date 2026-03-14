"""Tests unitaires du modèle GameAnswer — introspection des champs."""

from unittest.mock import MagicMock

from django.db import models

from apps.games.models import GameAnswer
from tests.base import BaseModelUnitTest


class TestGameAnswerModel(BaseModelUnitTest):
    """Vérifie les champs, contraintes et métadonnées du modèle GameAnswer."""

    def get_model_class(self):
        return GameAnswer

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champs ──────────────────────────────────────────────────────

    def test_answer_max_length(self):
        self.assert_field_max_length(GameAnswer, "answer", 255)

    def test_is_correct_default(self):
        self.assert_field_default(GameAnswer, "is_correct", False)

    def test_is_correct_db_index(self):
        self.assert_field_db_index(GameAnswer, "is_correct", True)

    def test_points_earned_default(self):
        self.assert_field_default(GameAnswer, "points_earned", 0)

    def test_streak_bonus_default(self):
        self.assert_field_default(GameAnswer, "streak_bonus", 0)

    def test_response_time_type(self):
        self.assert_field_type(GameAnswer, "response_time", models.FloatField)

    # ── Timestamps ──────────────────────────────────────────────────

    def test_answered_at_auto_now_add(self):
        field = GameAnswer._meta.get_field("answered_at")
        assert field.auto_now_add is True

    # ── ForeignKeys ─────────────────────────────────────────────────

    def test_round_cascade(self):
        field = GameAnswer._meta.get_field("round")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    def test_player_cascade(self):
        field = GameAnswer._meta.get_field("player")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("réponse", "réponses")

    def test_unique_together(self):
        self.assert_unique_together(GameAnswer, ["round", "player"])

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        mock_user = MagicMock()
        mock_user.username = "alice"
        mock_player = MagicMock()
        mock_player.user = mock_user
        mock_round = MagicMock()
        mock_round.round_number = 5
        answer = MagicMock(spec=GameAnswer)
        answer.player = mock_player
        answer.round = mock_round
        result = GameAnswer.__str__(answer)
        assert "alice" in result
        assert "5" in result
