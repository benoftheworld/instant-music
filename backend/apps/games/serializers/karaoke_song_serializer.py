"""Serializer for KaraokeSong."""

from rest_framework import serializers

from ..models import KaraokeSong


class KaraokeSongSerializer(serializers.ModelSerializer):
    """Serializer for KaraokeSong catalogue (read-only for players)."""

    duration_display = serializers.SerializerMethodField()

    class Meta:
        model = KaraokeSong
        fields = [
            "id",
            "title",
            "artist",
            "youtube_video_id",
            "lrclib_id",
            "album_image_url",
            "duration_ms",
            "duration_display",
            "is_active",
        ]

    def get_duration_display(self, obj):
        if not obj.duration_ms:
            return "--:--"
        total_seconds = obj.duration_ms // 1000
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}:{seconds:02d}"
