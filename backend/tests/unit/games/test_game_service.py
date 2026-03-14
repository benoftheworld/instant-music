"""Tests unitaires du GameService (check_answer, calculate_score)."""

from apps.games.services.game_service import GameService
from tests.base import BaseServiceUnitTest


class TestGameServiceCheckAnswer(BaseServiceUnitTest):
    """Vérifie la logique de vérification des réponses."""

    def get_service_module(self):
        import apps.games.services.game_service

        return apps.games.services.game_service

    def setup_method(self):
        self.service = GameService.__new__(GameService)

    # ── Mode Génération (guess_year) ────────────────────────────────

    def test_generation_exact_year(self):
        ok, factor = self.service.check_answer("generation", "1985", "1985")
        assert ok is True
        assert factor == 1.0

    def test_generation_off_by_1(self):
        ok, factor = self.service.check_answer("generation", "1986", "1985")
        assert ok is True
        assert factor == 0.75

    def test_generation_off_by_2(self):
        ok, factor = self.service.check_answer("generation", "1987", "1985")
        assert ok is True
        assert factor == 0.75

    def test_generation_off_by_3(self):
        ok, factor = self.service.check_answer("generation", "1988", "1985")
        assert ok is True
        assert factor == 0.4

    def test_generation_off_by_5(self):
        ok, factor = self.service.check_answer("generation", "1990", "1985")
        assert ok is True
        assert factor == 0.4

    def test_generation_off_by_6(self):
        ok, factor = self.service.check_answer("generation", "1991", "1985")
        assert ok is False
        assert factor == 0.0

    def test_generation_invalid_answer(self):
        ok, factor = self.service.check_answer("generation", "abc", "1985")
        assert ok is False
        assert factor == 0.0

    def test_generation_invalid_correct(self):
        ok, factor = self.service.check_answer("generation", "1985", "abc")
        assert ok is False
        assert factor == 0.0

    # ── Mode MCQ ────────────────────────────────────────────────────

    def test_mcq_exact_match(self):
        extra = {"answer_mode": "mcq"}
        ok, factor = self.service.check_answer(
            "classique", "Bohemian Rhapsody", "Bohemian Rhapsody", extra
        )
        assert ok is True
        assert factor == 1.0

    def test_mcq_wrong_answer(self):
        extra = {"answer_mode": "mcq"}
        ok, factor = self.service.check_answer(
            "classique", "Wrong", "Bohemian Rhapsody", extra
        )
        assert ok is False
        assert factor == 0.0

    # ── Mode texte (non classique/rapide) ───────────────────────────

    def test_text_fuzzy_match(self):
        extra = {"answer_mode": "text"}
        ok, factor = self.service.check_answer(
            "paroles", "Bohemian Rhapsodi", "Bohemian Rhapsody", extra
        )
        assert ok is True
        assert factor > 0.0

    def test_text_no_match(self):
        extra = {"answer_mode": "text"}
        ok, factor = self.service.check_answer(
            "paroles", "zzzzz", "Bohemian Rhapsody", extra
        )
        assert ok is False
        assert factor == 0.0

    # ── Mode texte classique (artiste + titre) ──────────────────────

    def test_classique_text_both_parts(self):
        """Artiste + titre → accuracy_factor 2.0."""
        extra = {
            "answer_mode": "text",
            "artist_name": "Queen",
            "track_name": "Bohemian Rhapsody",
        }
        ok, factor = self.service.check_answer(
            "classique", "Queen - Bohemian Rhapsody", "Bohemian Rhapsody", extra
        )
        assert ok is True
        assert factor == 2.0

    def test_classique_text_title_only(self):
        """Titre seul → accuracy_factor 1.0."""
        extra = {
            "answer_mode": "text",
            "artist_name": "Queen",
            "track_name": "Bohemian Rhapsody",
        }
        ok, factor = self.service.check_answer(
            "classique", "Bohemian Rhapsody", "Bohemian Rhapsody", extra
        )
        assert ok is True
        assert factor == 1.0

    def test_classique_text_json_format(self):
        """Format JSON legacy {"artist": ..., "title": ...}."""
        import json

        extra = {
            "answer_mode": "text",
            "artist_name": "Queen",
            "track_name": "Bohemian Rhapsody",
        }
        answer = json.dumps({"artist": "Queen", "title": "Bohemian Rhapsody"})
        ok, factor = self.service.check_answer(
            "classique", answer, "Bohemian Rhapsody", extra
        )
        assert ok is True
        assert factor == 2.0

    def test_classique_text_empty_answer(self):
        extra = {
            "answer_mode": "text",
            "artist_name": "Queen",
            "track_name": "Bohemian Rhapsody",
        }
        ok, factor = self.service.check_answer(
            "classique", "", "Bohemian Rhapsody", extra
        )
        assert ok is False
        assert factor == 0.0

    # ── Default answer_mode → mcq ───────────────────────────────────

    def test_no_extra_data_defaults_mcq(self):
        ok, factor = self.service.check_answer("classique", "Answer", "Answer", None)
        assert ok is True
        assert factor == 1.0
