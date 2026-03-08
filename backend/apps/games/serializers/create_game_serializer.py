"""Serializer for creating a game."""

from __future__ import annotations

from rest_framework import serializers

from ..models import Game, KaraokeSong


class CreateGameSerializer(serializers.ModelSerializer):
    """Serializer for creating a game."""

    karaoke_song_id = serializers.PrimaryKeyRelatedField(
        queryset=KaraokeSong.objects.filter(is_active=True),
        source="karaoke_song",
        required=False,
        allow_null=True,
    )

    class Meta:
        model = Game
        fields = [
            "mode",
            "max_players",
            "num_rounds",
            "playlist_id",
            "playlist_name",
            "playlist_image_url",
            "karaoke_song_id",
            "is_online",
            "is_public",
            "is_party_mode",
            "answer_mode",
            "guess_target",
            "round_duration",
            "score_display_duration",
            "lyrics_words_count",
        ]

    def validate(self, data):
        """Cross-field validation and karaoke forced values."""
        mode = data.get("mode", "classique")
        if mode == "karaoke":
            if not data.get("karaoke_song"):
                raise serializers.ValidationError(
                    "Le mode karaoké nécessite un morceau sélectionné dans le catalogue."
                )
            data["is_online"] = False
            data["max_players"] = 1
            data["num_rounds"] = 1
            data["score_display_duration"] = 0
            # Karaoké incompatible avec le mode soirée
            data["is_party_mode"] = False
        else:
            if not data.get("playlist_id"):
                raise serializers.ValidationError(
                    "Veuillez sélectionner une playlist."
                )
            # Mode soirée : nécessite une partie en ligne
            if data.get("is_party_mode") and not data.get("is_online", True):
                raise serializers.ValidationError(
                    "Le mode soirée nécessite une partie en ligne."
                )
            # Mode hors ligne (solo) : forcer 1 joueur max et partie privée
            if not data.get("is_online", True):
                data["max_players"] = 1
                data["is_public"] = False
                data["is_party_mode"] = False

        return data

    def validate_round_duration(self, value):
        if value < 10 or value > 300:
            raise serializers.ValidationError(
                "La durée d'un round doit être entre 10 et 300 secondes."
            )
        return value

    def validate_score_display_duration(self, value):
        if value < 0 or value > 30:
            raise serializers.ValidationError(
                "Le temps d'affichage du score doit être entre 0 et 30 secondes."
            )
        return value

    def validate_lyrics_words_count(self, value):
        if value < 2 or value > 10:
            raise serializers.ValidationError(
                "Le nombre de mots à deviner doit être entre 2 et 10."
            )
        return value

    def create(self, validated_data):
        """Always force timer_start_round=5 and populate legacy karaoke_track JSON."""
        validated_data["timer_start_round"] = 5
        song: KaraokeSong | None = validated_data.get("karaoke_song")
        if song:
            validated_data["karaoke_track"] = {
                "youtube_video_id": song.youtube_video_id,
                "track_name": song.title,
                "artist_name": song.artist,
                "duration_ms": song.duration_ms,
                "album_image": song.album_image_url,
                "lrclib_id": song.lrclib_id,
            }
        return super().create(validated_data)
