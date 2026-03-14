"""Tests unitaires de GameService.calculate_score et méthodes statiques."""

from apps.games.services.game_service import GameService
from tests.base import BaseUnitTest


class TestCalculateScoreMethod(BaseUnitTest):
    """Vérifie le calcul du score (Option C — Linear + Rank)."""

    def get_target_class(self):
        return GameService

    def setup_method(self):
        self.service = GameService()

    def test_zero_accuracy_returns_zero(self):
        assert self.service.calculate_score(0.0, 5.0) == 0

    def test_negative_accuracy_returns_zero(self):
        assert self.service.calculate_score(-1.0, 5.0) == 0

    def test_perfect_accuracy_fast_response(self):
        score = self.service.calculate_score(1.0, 0.0)
        assert score > 0

    def test_score_decreases_with_time(self):
        fast = self.service.calculate_score(1.0, 1.0)
        slow = self.service.calculate_score(1.0, 20.0)
        assert fast > slow

    def test_double_accuracy_factor(self):
        single = self.service.calculate_score(1.0, 5.0)
        double = self.service.calculate_score(2.0, 5.0)
        assert double > single

    def test_minimum_score_when_correct(self):
        # Even very slow, still gets minimum points
        score = self.service.calculate_score(1.0, 999.0)
        assert score > 0
