
"""Tests unitaires du CreateGameSerializer — validation croisée."""

from unittest.mock import MagicMock

from rest_framework import serializers as drf

from apps.games.serializers.create_game_serializer import CreateGameSerializer
from tests.base import BaseSerializerUnitTest


class TestCreateGameSerializer(BaseSerializerUnitTest):
    """Vérifie la validation croisée du serializer de création de partie."""

    def get_serializer_class(self):
        return CreateGameSerializer

    # ── validate_round_duration ─────────────────────────────────────

    def test_round_duration_too_low(self):
        serializer = CreateGameSerializer()
        try:
            serializer.validate_round_duration(5)
            pytest.fail("Should have raised")
        except drf.ValidationError:
            pass

    def test_round_duration_too_high(self):
        serializer = CreateGameSerializer()
        try:
            serializer.validate_round_duration(301)
            pytest.fail("Should have raised")
        except drf.ValidationError:
            pass

    def test_round_duration_valid_min(self):
        assert CreateGameSerializer().validate_round_duration(10) == 10

    def test_round_duration_valid_max(self):
        assert CreateGameSerializer().validate_round_duration(300) == 300

    # ── validate_score_display_duration ──────────────────────────────

    def test_score_display_too_low(self):
        serializer = CreateGameSerializer()
        try:
            serializer.validate_score_display_duration(-1)
            pytest.fail("Should have raised")
        except drf.ValidationError:
            pass

    def test_score_display_too_high(self):
        serializer = CreateGameSerializer()
        try:
            serializer.validate_score_display_duration(31)
            pytest.fail("Should have raised")
        except drf.ValidationError:
            pass

    def test_score_display_valid(self):
        assert CreateGameSerializer().validate_score_display_duration(15) == 15

    # ── validate_lyrics_words_count ─────────────────────────────────

    def test_lyrics_words_too_low(self):
        serializer = CreateGameSerializer()
        try:
            serializer.validate_lyrics_words_count(1)
            pytest.fail("Should have raised")
        except drf.ValidationError:
            pass

    def test_lyrics_words_too_high(self):
        serializer = CreateGameSerializer()
        try:
            serializer.validate_lyrics_words_count(11)
            pytest.fail("Should have raised")
        except drf.ValidationError:
            pass

    def test_lyrics_words_valid(self):
        assert CreateGameSerializer().validate_lyrics_words_count(5) == 5

    # ── validate() cross-field ──────────────────────────────────────

    def test_karaoke_requires_song(self):
        serializer = CreateGameSerializer()
        try:
            serializer.validate({"mode": "karaoke"})
            pytest.fail("Should have raised")
        except drf.ValidationError:
            pass

    def test_karaoke_forces_offline_settings(self):
        serializer = CreateGameSerializer()
        song = MagicMock()
        data = serializer.validate(
            {
                "mode": "karaoke",
                "karaoke_song": song,
                "is_online": True,
                "max_players": 10,
            }
        )
        assert data["is_online"] is False
        assert data["max_players"] == 1
        assert data["num_rounds"] == 1
        assert data["is_party_mode"] is False

    def test_classic_requires_playlist(self):
        serializer = CreateGameSerializer()
        try:
            serializer.validate({"mode": "classique"})
            pytest.fail("Should have raised")
        except drf.ValidationError:
            pass

    def test_party_mode_requires_online(self):
        serializer = CreateGameSerializer()
        try:
            serializer.validate(
                {
                    "mode": "classique",
                    "playlist_id": "123",
                    "is_party_mode": True,
                    "is_online": False,
                }
            )
            pytest.fail("Should have raised")
        except drf.ValidationError:
            pass

    def test_offline_forces_solo_settings(self):
        serializer = CreateGameSerializer()
        data = serializer.validate(
            {
                "mode": "classique",
                "playlist_id": "123",
                "is_online": False,
                "max_players": 10,
                "is_public": True,
            }
        )
        assert data["max_players"] == 1
        assert data["is_public"] is False
        assert data["is_party_mode"] is False
        assert data["bonuses_enabled"] is False

    def test_valid_online_classic(self):
        serializer = CreateGameSerializer()
        data = serializer.validate(
            {
                "mode": "classique",
                "playlist_id": "123",
                "is_online": True,
            }
        )
        assert data["playlist_id"] == "123"
