"""Tests unitaires de GameService._effective_round_duration et helpers statiques."""

from apps.games.services.game_service import GameService
from apps.games.services.scoring import KARAOKE_FALLBACK_DURATION, KARAOKE_MAX_DURATION
from tests.base import BaseUnitTest


class TestEffectiveRoundDuration(BaseUnitTest):
    """Vérifie le calcul de durée effective d'un round."""

    def get_target_class(self):
        return GameService._effective_round_duration

    def test_non_karaoke_returns_default(self):
        result = GameService._effective_round_duration(
            {"extra_data": {}}, is_karaoke=False, default_duration=30
        )
        assert result == 30

    def test_karaoke_with_video_duration(self):
        question = {"extra_data": {"video_duration_ms": 180000}}  # 3 min
        result = GameService._effective_round_duration(
            question, is_karaoke=True, default_duration=30
        )
        assert result == 180000 // 1000 + 5  # 185s

    def test_karaoke_caps_at_max(self):
        question = {"extra_data": {"video_duration_ms": 999999999}}
        result = GameService._effective_round_duration(
            question, is_karaoke=True, default_duration=30
        )
        assert result == KARAOKE_MAX_DURATION

    def test_karaoke_zero_duration_falls_back(self):
        question = {"extra_data": {"video_duration_ms": 0}}
        result = GameService._effective_round_duration(
            question, is_karaoke=True, default_duration=30
        )
        assert result == KARAOKE_FALLBACK_DURATION

    def test_karaoke_no_video_duration_key(self):
        result = GameService._effective_round_duration(
            {"extra_data": {}}, is_karaoke=True, default_duration=30
        )
        assert result == KARAOKE_FALLBACK_DURATION
