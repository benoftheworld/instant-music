"""Serializer for Game."""

from rest_framework import serializers

from ..models import Game
from .karaoke_song_serializer import KaraokeSongSerializer
from .game_player_serializer import GamePlayerSerializer


class GameSerializer(serializers.ModelSerializer):
    """Serializer for Game."""

    players = GamePlayerSerializer(many=True, read_only=True)
    host_username = serializers.CharField(
        source="host.username", read_only=True
    )
    player_count = serializers.SerializerMethodField()
    karaoke_song_detail = KaraokeSongSerializer(
        source="karaoke_song", read_only=True
    )

    class Meta:
        model = Game
        fields = [
            "id",
            "name",
            "room_code",
            "host",
            "host_username",
            "mode",
            "status",
            "max_players",
            "num_rounds",
            "playlist_id",
            "playlist_name",
            "playlist_image_url",
            "karaoke_track",
            "karaoke_song",
            "karaoke_song_detail",
            "is_online",
            "is_public",
            "answer_mode",
            "guess_target",
            "round_duration",
            "timer_start_round",
            "score_display_duration",
            "lyrics_words_count",
            "players",
            "player_count",
            "created_at",
            "started_at",
            "finished_at",
        ]
        read_only_fields = ["id", "room_code", "created_at"]

    def get_player_count(self, obj):
        """Get number of players in the game."""
        return obj.players.count()
