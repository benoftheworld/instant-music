"""Serializer for game history."""

from rest_framework import serializers

from ..models import Game


class GameHistorySerializer(serializers.ModelSerializer):
    """Serializer for game history with full details."""

    winner = serializers.SerializerMethodField()
    winner_score = serializers.SerializerMethodField()
    player_count = serializers.SerializerMethodField()
    mode_display = serializers.CharField(
        source="get_mode_display", read_only=True
    )
    host_username = serializers.CharField(
        source="host.username", read_only=True
    )
    participants = serializers.SerializerMethodField()
    answer_mode_display = serializers.CharField(
        source="get_answer_mode_display", read_only=True
    )
    guess_target_display = serializers.CharField(
        source="get_guess_target_display", read_only=True
    )

    class Meta:
        model = Game
        fields = [
            "id",
            "room_code",
            "host_username",
            "mode",
            "mode_display",
            "answer_mode",
            "answer_mode_display",
            "guess_target",
            "guess_target_display",
            "num_rounds",
            "playlist_id",
            "winner",
            "winner_score",
            "player_count",
            "participants",
            "created_at",
            "started_at",
            "finished_at",
        ]

    def _sorted_players(self, obj):
        """Tri en mémoire sur le prefetch — évite toute requête DB supplémentaire.

        Nécessite que le queryset appelant prefetch_related("players__user").
        """
        return sorted(obj.players.all(), key=lambda p: p.score, reverse=True)

    def get_winner(self, obj):
        """Get the winner of the game."""
        players = self._sorted_players(obj)
        if not players:
            return None
        top = players[0]
        return {
            "id": top.user.id,
            "username": top.user.username,
            "avatar": top.user.avatar.url if top.user.avatar else None,
        }

    def get_winner_score(self, obj):
        """Get the winner's score."""
        players = self._sorted_players(obj)
        return players[0].score if players else 0

    def get_player_count(self, obj):
        """Get number of players in the game."""
        return len(obj.players.all())

    def get_participants(self, obj):
        """Get list of all participants with their rankings."""
        return [
            {
                "id": player.user.id,
                "username": player.user.username,
                "avatar": (
                    player.user.avatar.url if player.user.avatar else None
                ),
                "score": player.score,
                "rank": idx + 1,
            }
            for idx, player in enumerate(self._sorted_players(obj))
        ]
