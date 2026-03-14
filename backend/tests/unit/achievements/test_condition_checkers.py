"""Tests unitaires des condition checkers purs de achievements (simples)."""

from unittest.mock import MagicMock

from apps.achievements.services import (
    _check_games_played,
    _check_points,
    _check_wins,
)
from tests.base import BaseUnitTest


class TestCheckGamesPlayed(BaseUnitTest):
    """Vérifie _check_games_played, _check_wins, _check_points."""

    def get_target_class(self):
        return _check_games_played

    def test_enough_games(self):
        user = MagicMock(total_games_played=10)
        assert _check_games_played(user, 5, None, None, None) is True

    def test_not_enough_games(self):
        user = MagicMock(total_games_played=3)
        assert _check_games_played(user, 5, None, None, None) is False

    def test_exact_threshold(self):
        user = MagicMock(total_games_played=5)
        assert _check_games_played(user, 5, None, None, None) is True

    def test_wins_enough(self):
        user = MagicMock(total_wins=10)
        assert _check_wins(user, 5, None, None, None) is True

    def test_wins_not_enough(self):
        user = MagicMock(total_wins=2)
        assert _check_wins(user, 5, None, None, None) is False

    def test_points_enough(self):
        user = MagicMock(total_points=1000)
        assert _check_points(user, 500, None, None, None) is True

    def test_points_not_enough(self):
        user = MagicMock(total_points=100)
        assert _check_points(user, 500, None, None, None) is False
