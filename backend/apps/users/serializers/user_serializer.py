"""User serializers."""

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from ..models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model — usage restreint aux vues 'self' et admin.

    Pour les vues publiques (listes, profils d'autres joueurs), utiliser
    PublicUserSerializer qui n'expose ni email ni is_staff.
    """

    win_rate = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
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
        ]
        read_only_fields = [
            "id",
            "is_staff",
            "total_games_played",
            "total_wins",
            "total_points",
            "coins_balance",
            "created_at",
            "updated_at",
        ]


class PublicUserSerializer(serializers.ModelSerializer):
    """Serializer public — n'expose ni email ni is_staff."""

    win_rate = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "avatar",
            "total_games_played",
            "total_wins",
            "total_points",
            "coins_balance",
            "win_rate",
            "created_at",
        ]
        read_only_fields = fields


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for lists."""

    class Meta:
        model = User
        fields = ["id", "username", "avatar", "total_points", "total_wins"]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""

    class Meta:
        model = User
        fields = ["avatar"]


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        """Validate new password avec les validateurs Django."""
        validate_password(value)
        return value
