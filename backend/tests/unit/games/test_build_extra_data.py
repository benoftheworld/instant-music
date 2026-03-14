"""Tests unitaires de GameService._build_extra_data et _resolve_options."""

from unittest.mock import MagicMock

from apps.games.services.game_service import GameService
from tests.base import BaseUnitTest


class TestBuildExtraData(BaseUnitTest):
    """Vérifie la construction de extra_data pour les rounds."""

    def get_target_class(self):
        return GameService._build_extra_data

    def test_basic_fields_set(self):
        question = {
            "extra_data": {},
            "artist_name": "Queen",
            "track_name": "Bohemian Rhapsody",
            "_mode": "classique",
        }
        game = MagicMock(mode="classique", answer_mode="mcq", guess_target="title")
        result = GameService._build_extra_data(question, game)
        assert result["artist_name"] == "Queen"
        assert result["track_name"] == "Bohemian Rhapsody"
        assert result["round_mode"] == "classique"
        assert result["answer_mode"] == "mcq"
        assert result["guess_target"] == "title"

    def test_preserves_existing_album_image(self):
        question = {
            "extra_data": {"album_image": "existing.jpg"},
            "album_image": "should_not_override.jpg",
            "artist_name": "A",
            "track_name": "T",
        }
        game = MagicMock(mode="classique", answer_mode="mcq", guess_target="title")
        result = GameService._build_extra_data(question, game)
        assert result["album_image"] == "existing.jpg"

    def test_adds_album_image_from_question(self):
        question = {
            "extra_data": {},
            "album_image": "from_question.jpg",
            "artist_name": "A",
            "track_name": "T",
        }
        game = MagicMock(mode="classique", answer_mode="mcq", guess_target="title")
        result = GameService._build_extra_data(question, game)
        assert result["album_image"] == "from_question.jpg"

    def test_fallback_mode_from_game(self):
        question = {
            "extra_data": {},
            "artist_name": "A",
            "track_name": "T",
        }
        game = MagicMock(mode="rapide", answer_mode="text", guess_target="artist")
        result = GameService._build_extra_data(question, game)
        assert result["round_mode"] == "rapide"
