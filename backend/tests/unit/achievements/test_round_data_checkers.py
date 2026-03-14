"""Tests unitaires des condition checkers round_data."""

from apps.achievements.services import (
    _check_all_fast_round,
    _check_dominant_win,
    _check_in_game_streak,
    _check_perfect_round,
)
from tests.base import BaseUnitTest


class TestCheckRoundDataConditions(BaseUnitTest):
    """Vérifie les checkers basés sur round_data."""

    def get_target_class(self):
        return _check_perfect_round

    def test_perfect_game(self):
        assert _check_perfect_round(None, 0, None, None, {"perfect_game": True}) is True

    def test_not_perfect(self):
        assert _check_perfect_round(None, 0, None, None, {"perfect_game": False}) is False

    def test_no_round_data(self):
        assert _check_perfect_round(None, 0, None, None, None) is False

    def test_all_fast_perfect_and_fast(self):
        rd = {"perfect_game": True, "max_response_time": 1.5}
        assert _check_all_fast_round(None, 0, "2.0", None, rd) is True

    def test_all_fast_perfect_but_slow(self):
        rd = {"perfect_game": True, "max_response_time": 3.0}
        assert _check_all_fast_round(None, 0, "2.0", None, rd) is False

    def test_all_fast_not_perfect(self):
        rd = {"perfect_game": False, "max_response_time": 1.0}
        assert _check_all_fast_round(None, 0, "2.0", None, rd) is False

    def test_all_fast_default_threshold(self):
        rd = {"perfect_game": True, "max_response_time": 1.5}
        assert _check_all_fast_round(None, 0, None, None, rd) is True

    def test_in_game_streak_met(self):
        assert _check_in_game_streak(None, 5, None, None, {"max_streak": 7}) is True

    def test_in_game_streak_not_met(self):
        assert _check_in_game_streak(None, 5, None, None, {"max_streak": 3}) is False

    def test_in_game_streak_no_data(self):
        assert _check_in_game_streak(None, 5, None, None, None) is False

    def test_dominant_win_true(self):
        assert _check_dominant_win(None, 0, None, None, {"dominant_win": True}) is True

    def test_dominant_win_false(self):
        assert _check_dominant_win(None, 0, None, None, {"dominant_win": False}) is False

    def test_dominant_win_no_data(self):
        assert _check_dominant_win(None, 0, None, None, None) is False
