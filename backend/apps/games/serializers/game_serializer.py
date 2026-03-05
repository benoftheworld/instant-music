"""Serializer for Game."""

from rest_framework import serializers

from ..models import Game
from .game_player_serializer import GamePlayerSerializer
from .karaoke_song_serializer import KaraokeSongSerializer


class GameSerializer(serializers.ModelSerializer):
    """Serializer for Game."""

    players = GamePlayerSerializer(many=True, read_only=True)
    host_username = serializers.CharField(source="host.username", read_only=True)
    player_count = serializers.SerializerMethodField()
    karaoke_song_detail = KaraokeSongSerializer(source="karaoke_song", read_only=True)

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
        """Get number of players in the game.

        Utilise l'annotation `player_count` si disponible (via Count('players')
        dans le queryset) pour éviter un N+1 query. Fallback sur len() si
        les players sont prefetch_related, sinon .count().
        """
        # Annotation depuis le viewset (optimal)
        if hasattr(obj, "_player_count"):
            return obj._player_count
        # prefetch_related déjà chargé (pas de query supplémentaire)
        if "players" in getattr(obj, "_prefetched_objects_cache", {}):
            return len(obj.players.all())
        return obj.players.count()
