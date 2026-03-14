"""Tests unitaires du LeaderboardSerializer."""

from apps.games.serializers.leaderboard_serializer import LeaderboardSerializer
from tests.base import BaseSerializerUnitTest


class TestLeaderboardSerializer(BaseSerializerUnitTest):
    """Vérifie les champs du serializer de classement."""

    def get_serializer_class(self):
        return LeaderboardSerializer

    def test_fields(self):
        serializer = LeaderboardSerializer()
        expected = {
            "user_id",
            "username",
            "avatar",
            "total_games",
            "total_wins",
            "total_points",
            "win_rate",
        }
        assert set(serializer.fields.keys()) == expected

    def test_valid_data(self):
        data = {
            "user_id": 1,
            "username": "player1",
            "avatar": None,
            "total_games": 10,
            "total_wins": 5,
            "total_points": 500,
            "win_rate": 50.0,
        }
        serializer = LeaderboardSerializer(data=data)
        assert serializer.is_valid()

    def test_avatar_allow_null(self):
        serializer = LeaderboardSerializer()
        assert serializer.fields["avatar"].allow_null is True
