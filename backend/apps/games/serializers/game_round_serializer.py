"""Serializer for GameRound."""

from rest_framework import serializers

from ..models import GameRound


class GameRoundSerializer(serializers.ModelSerializer):
    """Serializer for GameRound (hides correct answer during play)."""

    class Meta:
        model = GameRound
        fields = [
            "id",
            "game",
            "round_number",
            "track_id",
            "track_name",
            "artist_name",
            "options",
            "preview_url",
            "question_type",
            "question_text",
            "extra_data",
            "duration",
            "started_at",
            "ended_at",
        ]
        read_only_fields = ["id", "started_at"]
