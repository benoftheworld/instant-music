"""Tests unitaires du UserDetailedStatsSerializer."""

from apps.stats.serializers import UserDetailedStatsSerializer
from tests.base import BaseSerializerUnitTest


class TestUserDetailedStatsSerializer(BaseSerializerUnitTest):
    """Vérifie les champs du serializer de statistiques détaillées."""

    def get_serializer_class(self):
        return UserDetailedStatsSerializer

    def test_fields(self):
        serializer = UserDetailedStatsSerializer()
        expected = {
            "total_games_played",
            "total_wins",
            "total_points",
            "win_rate",
            "avg_score_per_game",
            "best_score",
            "total_correct_answers",
            "total_answers",
            "accuracy",
            "avg_response_time",
            "achievements_unlocked",
            "achievements_total",
        }
        assert set(serializer.fields.keys()) == expected

    def test_valid_data(self):
        data = {
            "total_games_played": 100,
            "total_wins": 50,
            "total_points": 5000,
            "win_rate": 50.0,
            "avg_score_per_game": 50.0,
            "best_score": 200,
            "total_correct_answers": 300,
            "total_answers": 500,
            "accuracy": 60.0,
            "avg_response_time": 3.5,
            "achievements_unlocked": 10,
            "achievements_total": 25,
        }
        serializer = UserDetailedStatsSerializer(data=data)
        assert serializer.is_valid()
