"""GameInvitation serializer."""

from rest_framework import serializers

from apps.users.models import User

from ..models import GameInvitation


class UserMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class GameInvitationSerializer(serializers.ModelSerializer):
    sender = UserMiniSerializer(read_only=True)
    recipient = UserMiniSerializer(read_only=True)
    room_code = serializers.CharField(source="game.room_code", read_only=True)
    game_mode = serializers.CharField(source="game.mode", read_only=True)
    game_name = serializers.CharField(source="game.name", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)

    class Meta:
        model = GameInvitation
        fields = [
            "id",
            "room_code",
            "game_mode",
            "game_name",
            "sender",
            "recipient",
            "status",
            "created_at",
            "expires_at",
            "is_expired",
        ]
