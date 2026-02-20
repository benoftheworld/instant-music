"""
Serializers for games.
"""

from rest_framework import serializers
from .models import Game, GamePlayer, GameRound, GameAnswer


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


class GameSerializer(serializers.ModelSerializer):
    """Serializer for Game."""

    players = GamePlayerSerializer(many=True, read_only=True)
    host_username = serializers.CharField(
        source="host.username", read_only=True
    )
    player_count = serializers.SerializerMethodField()

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
            "karaoke_track",
            "is_online",
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


class CreateGameSerializer(serializers.ModelSerializer):
    """Serializer for creating a game."""

    class Meta:
        model = Game
        fields = [
            "name",
            "mode",
            "max_players",
            "num_rounds",
            "playlist_id",
            "karaoke_track",
            "is_online",
            "answer_mode",
            "guess_target",
            "round_duration",
            "timer_start_round",
            "score_display_duration",
            "lyrics_words_count",
        ]

    def validate(self, data):
        """Cross-field validation: karaoke needs karaoke_track, others need playlist_id."""
        mode = data.get("mode", "classique")
        if mode == "karaoke":
            karaoke_track = data.get("karaoke_track")
            if not karaoke_track or not karaoke_track.get("youtube_video_id"):
                raise serializers.ValidationError(
                    "Le mode karaoké nécessite un morceau YouTube sélectionné."
                )
        else:
            if not data.get("playlist_id"):
                raise serializers.ValidationError(
                    "Veuillez sélectionner une playlist."
                )
        return data

    def validate_round_duration(self, value):
        if value < 10 or value > 300:
            raise serializers.ValidationError(
                "La durée d'un round doit être entre 10 et 300 secondes."
            )
        return value

    def validate_timer_start_round(self, value):
        if value < 3 or value > 15:
            raise serializers.ValidationError(
                "Le timer de début de round doit être entre 3 et 15 secondes."
            )
        return value

    def validate_score_display_duration(self, value):
        if value < 3 or value > 30:
            raise serializers.ValidationError(
                "Le temps d'affichage du score doit être entre 3 et 30 secondes."
            )
        return value

    def validate_lyrics_words_count(self, value):
        if value < 2 or value > 10:
            raise serializers.ValidationError(
                "Le nombre de mots à deviner doit être entre 2 et 10."
            )
        return value


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


class GameRoundResultSerializer(serializers.ModelSerializer):
    """Serializer for GameRound with correct answer revealed."""

    class Meta:
        model = GameRound
        fields = [
            "id",
            "game",
            "round_number",
            "track_id",
            "track_name",
            "artist_name",
            "correct_answer",
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


class LeaderboardSerializer(serializers.Serializer):
    """Serializer for leaderboard data."""

    user_id = serializers.IntegerField()
    username = serializers.CharField()
    avatar = serializers.CharField(allow_null=True)
    total_games = serializers.IntegerField()
    total_wins = serializers.IntegerField()
    total_points = serializers.IntegerField()
    win_rate = serializers.FloatField()
