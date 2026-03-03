"""User serializers."""

from rest_framework import serializers

from ..models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""

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
        """Validate new password."""
        if len(value) < 8:
            raise serializers.ValidationError(
                "Le mot de passe doit contenir au moins 8 caractères."
            )
        return value
