"""Tests unitaires du module scoring."""

from apps.games.services.scoring import (
    SCORE_BASE_POINTS,
    SCORE_MIN_CORRECT,
    SCORE_MIN_FINAL,
    SCORE_STREAK_BONUS_PER_LEVEL,
    SCORE_STREAK_MAX_LEVEL,
    SCORE_TIME_PENALTY_PER_SEC,
)
from tests.base import BaseServiceUnitTest


class TestScoringConstants(BaseServiceUnitTest):
    """Vérifie les constantes de scoring."""

    def get_service_module(self):
        import apps.games.services.scoring

        return apps.games.services.scoring

    def test_base_points(self):
        assert SCORE_BASE_POINTS == 100

    def test_time_penalty(self):
        assert SCORE_TIME_PENALTY_PER_SEC == 3

    def test_min_correct(self):
        assert SCORE_MIN_CORRECT == 10

    def test_min_final(self):
        assert SCORE_MIN_FINAL == 5

    def test_streak_bonus_per_level(self):
        assert SCORE_STREAK_BONUS_PER_LEVEL == 10

    def test_streak_max_level(self):
        assert SCORE_STREAK_MAX_LEVEL == 5
