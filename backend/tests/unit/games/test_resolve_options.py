"""Tests unitaires de GameService._resolve_options."""

from apps.games.services.game_service import GameService
from tests.base import BaseUnitTest


class TestResolveOptions(BaseUnitTest):
    """Vérifie la résolution des options MCQ."""

    def get_target_class(self):
        return GameService._resolve_options

    def test_normal_mcq(self):
        question = {"options": ["A", "B", "C", "D"]}
        result = GameService._resolve_options(
            question, is_karaoke=False, is_text_mode=False
        )
        assert result == ["A", "B", "C", "D"]

    def test_karaoke_returns_empty(self):
        question = {"options": ["A", "B", "C", "D"]}
        result = GameService._resolve_options(
            question, is_karaoke=True, is_text_mode=False
        )
        assert result == []

    def test_text_mode_returns_empty(self):
        question = {"options": ["A", "B", "C", "D"]}
        result = GameService._resolve_options(
            question, is_karaoke=False, is_text_mode=True
        )
        assert result == []

    def test_both_karaoke_and_text_returns_empty(self):
        question = {"options": ["A", "B", "C", "D"]}
        result = GameService._resolve_options(
            question, is_karaoke=True, is_text_mode=True
        )
        assert result == []
