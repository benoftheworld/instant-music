"""Serializer for GamePlayer."""

from rest_framework import serializers

from ..models import GamePlayer


class GamePlayerSerializer(serializers.ModelSerializer):
    """Serializer for GamePlayer."""

    username = serializers.CharField(source="user.username", read_only=True)
    avatar = serializers.ImageField(source="user.avatar", read_only=True)

    class Meta:
        model = GamePlayer
        fields = [
            "id",
            "user",
            "username",
            "avatar",
            "score",
            "rank",
            "is_connected",
            "joined_at",
        ]
        read_only_fields = ["id", "score", "rank", "joined_at"]
