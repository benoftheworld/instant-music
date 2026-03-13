"""Friendship serializers."""

from rest_framework import serializers

from ..models import Friendship, User
from .user_serializer import UserMinimalSerializer


class FriendshipSerializer(serializers.ModelSerializer):
    """Serializer for Friendship model."""

    from_user = UserMinimalSerializer(read_only=True)
    to_user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = Friendship
        fields = [
            "id",
            "from_user",
            "to_user",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "from_user",
            "status",
            "created_at",
            "updated_at",
        ]


class FriendshipCreateSerializer(serializers.Serializer):
    """Serializer for creating a friendship request."""

    username = serializers.CharField(required=True)

    def validate_username(self, value):
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable.")
        return value
