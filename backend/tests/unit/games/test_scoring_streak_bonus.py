"""Tests unitaires du calcul de bonus de série."""

from apps.games.services.scoring import calculate_streak_bonus
from tests.base import BaseServiceUnitTest


class TestCalculateStreakBonus(BaseServiceUnitTest):
    """Vérifie le calcul du bonus de série."""

    def get_service_module(self):
        import apps.games.services.scoring
        return apps.games.services.scoring

    def test_streak_0_no_bonus(self):
        assert calculate_streak_bonus(0) == 0

    def test_streak_1_no_bonus(self):
        """Première bonne réponse = streak 1 → level 0."""
        assert calculate_streak_bonus(1) == 0

    def test_streak_2_level_1(self):
        assert calculate_streak_bonus(2) == 10

    def test_streak_3_level_2(self):
        assert calculate_streak_bonus(3) == 20

    def test_streak_6_capped(self):
        """Streak 6 → level 5 (plafond) → 50."""
        assert calculate_streak_bonus(6) == 50

    def test_streak_10_capped(self):
        """Au-delà du plafond, le bonus reste à 50."""
        assert calculate_streak_bonus(10) == 50

    def test_negative_streak(self):
        """Streak négatif → 0."""
        assert calculate_streak_bonus(-1) == 0
