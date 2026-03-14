"""Tests unitaires du GameService — calculate_score."""

from apps.games.services.game_service import GameService
from tests.base import BaseServiceUnitTest


class TestGameServiceCalculateScore(BaseServiceUnitTest):
    """Vérifie le calcul des points."""

    def get_service_module(self):
        import apps.games.services.game_service
        return apps.games.services.game_service

    def setup_method(self):
        self.service = GameService.__new__(GameService)

    def test_zero_accuracy_returns_zero(self):
        assert self.service.calculate_score(0.0, 5.0) == 0

    def test_negative_accuracy_returns_zero(self):
        assert self.service.calculate_score(-0.5, 5.0) == 0

    def test_perfect_instant_answer(self):
        """accuracy=1.0, response_time=0 → 100 points."""
        score = self.service.calculate_score(1.0, 0.0)
        assert score == 100

    def test_time_penalty(self):
        """10 secondes → 100 - 30 = 70 points."""
        score = self.service.calculate_score(1.0, 10.0)
        assert score == 70

    def test_min_correct_floor(self):
        """Temps long → plafonné à SCORE_MIN_CORRECT (10)."""
        score = self.service.calculate_score(1.0, 50.0)
        assert score == 10

    def test_accuracy_factor_applied(self):
        """accuracy=0.5 → score réduit de moitié."""
        score = self.service.calculate_score(0.5, 0.0)
        assert score == 50

    def test_double_points_factor(self):
        """accuracy=2.0 → double les points."""
        score = self.service.calculate_score(2.0, 0.0)
        assert score == 200

    def test_min_final_floor(self):
        """Score ne descend jamais sous SCORE_MIN_FINAL (5)."""
        score = self.service.calculate_score(0.01, 50.0)
        assert score >= 5
