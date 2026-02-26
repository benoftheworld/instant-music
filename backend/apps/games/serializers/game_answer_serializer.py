"""Serializer for GameAnswer."""

from rest_framework import serializers

from ..models import GameAnswer


class GameAnswerSerializer(serializers.ModelSerializer):
    """Serializer for GameAnswer."""

    class Meta:
        model = GameAnswer
        fields = [
            "id",
            "round",
            "player",
            "answer",
            "is_correct",
            "points_earned",
            "response_time",
            "answered_at",
        ]
        read_only_fields = ["id", "is_correct", "points_earned", "answered_at"]
