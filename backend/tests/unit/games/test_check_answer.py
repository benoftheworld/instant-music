"""Tests unitaires de GameService.check_answer."""

from apps.games.services.game_service import GameService
from tests.base import BaseUnitTest


class TestCheckAnswer(BaseUnitTest):
    """Vérifie la logique de vérification des réponses."""

    def get_target_class(self):
        return GameService

    def setup_method(self):
        self.service = GameService()

    # ── Mode GENERATION ──

    def test_generation_exact(self):
        is_correct, factor = self.service.check_answer("generation", "1985", "1985")
        assert is_correct is True
        assert factor == 1.0

    def test_generation_close_within_2(self):
        is_correct, factor = self.service.check_answer("generation", "1987", "1985")
        assert is_correct is True
        assert factor == 0.75

    def test_generation_close_within_5(self):
        is_correct, factor = self.service.check_answer("generation", "1990", "1985")
        assert is_correct is True
        assert factor == 0.4

    def test_generation_wrong(self):
        is_correct, factor = self.service.check_answer("generation", "2000", "1985")
        assert is_correct is False
        assert factor == 0.0

    def test_generation_invalid_input(self):
        is_correct, factor = self.service.check_answer("generation", "abc", "1985")
        assert is_correct is False
        assert factor == 0.0

    # ── Mode MCQ ──

    def test_mcq_correct(self):
        is_correct, factor = self.service.check_answer(
            "classique", "Answer A", "Answer A", {"answer_mode": "mcq"}
        )
        assert is_correct is True
        assert factor == 1.0

    def test_mcq_wrong(self):
        is_correct, factor = self.service.check_answer(
            "classique", "Answer B", "Answer A", {"answer_mode": "mcq"}
        )
        assert is_correct is False
        assert factor == 0.0

    # ── Mode TEXT classique ──

    def test_text_classique_both_artist_and_title(self):
        extra = {
            "answer_mode": "text",
            "artist_name": "Queen",
            "track_name": "Bohemian Rhapsody",
        }
        is_correct, factor = self.service.check_answer(
            "classique", "Queen - Bohemian Rhapsody", "Bohemian Rhapsody", extra
        )
        assert is_correct is True
        assert factor == 2.0

    def test_text_classique_title_only(self):
        extra = {
            "answer_mode": "text",
            "artist_name": "Queen",
            "track_name": "Bohemian Rhapsody",
        }
        is_correct, factor = self.service.check_answer(
            "classique", "Bohemian Rhapsody", "Bohemian Rhapsody", extra
        )
        assert is_correct is True
        assert factor == 1.0

    def test_text_classique_wrong(self):
        extra = {
            "answer_mode": "text",
            "artist_name": "Queen",
            "track_name": "Bohemian Rhapsody",
        }
        is_correct, factor = self.service.check_answer(
            "classique", "zzz xxx yyy", "Bohemian Rhapsody", extra
        )
        assert is_correct is False

    # ── Mode TEXT non classique ──

    def test_text_paroles_fuzzy(self):
        extra = {"answer_mode": "text"}
        is_correct, factor = self.service.check_answer(
            "paroles", "Bohemian Rhapsody", "Bohemian Rhapsody", extra
        )
        assert is_correct is True
        assert factor > 0
