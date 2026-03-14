"""Tests unitaires du UserSerializer."""

from apps.users.serializers.user_serializer import UserSerializer
from tests.base import BaseSerializerUnitTest


class TestUserSerializer(BaseSerializerUnitTest):
    """Vérifie les champs et read-only du UserSerializer."""

    def get_serializer_class(self):
        return UserSerializer

    def test_fields(self):
        serializer = UserSerializer()
        expected = {
            "id",
            "username",
            "email",
            "avatar",
            "is_staff",
            "total_games_played",
            "total_wins",
            "total_points",
            "coins_balance",
            "win_rate",
            "created_at",
            "updated_at",
        }
        assert set(serializer.fields.keys()) == expected

    def test_read_only_fields(self):
        serializer = UserSerializer()
        read_only = {
            "id",
            "is_staff",
            "total_games_played",
            "total_wins",
            "total_points",
            "coins_balance",
            "created_at",
            "updated_at",
        }
        for field_name in read_only:
            assert serializer.fields[field_name].read_only is True, (
                f"{field_name} devrait être read_only"
            )

    def test_win_rate_is_read_only(self):
        serializer = UserSerializer()
        assert serializer.fields["win_rate"].read_only is True
