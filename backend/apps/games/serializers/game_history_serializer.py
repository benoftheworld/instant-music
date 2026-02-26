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

    def get_winner(self, obj):
        """Get the winner of the game."""
        top_player = obj.players.order_by("-score").first()
        if top_player:
            return {
                "id": top_player.user.id,
                "username": top_player.user.username,
                "avatar": (
                    top_player.user.avatar.url
                    if top_player.user.avatar
                    else None
                ),
            }
        return None

    def get_winner_score(self, obj):
        """Get the winner's score."""
        top_player = obj.players.order_by("-score").first()
        return top_player.score if top_player else 0

    def get_player_count(self, obj):
        """Get number of players in the game."""
        return obj.players.count()

    def get_participants(self, obj):
        """Get list of all participants with their rankings."""
        players = obj.players.order_by("-score")
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
            for idx, player in enumerate(players)
        ]
