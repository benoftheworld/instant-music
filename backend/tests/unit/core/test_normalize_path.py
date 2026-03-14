"""Tests unitaires de _normalize_path."""

from apps.core.middleware import _normalize_path
from tests.base import BaseUnitTest


class TestNormalizePath(BaseUnitTest):
    """Vérifie la normalisation des chemins pour Prometheus."""

    def get_target_class(self):
        return _normalize_path

    def test_game_room_code(self):
        assert _normalize_path("/api/games/ABC123/") == "/api/games/{room_code}/"

    def test_user_id(self):
        assert _normalize_path("/api/users/42/") == "/api/users/{id}/"

    def test_achievement_id(self):
        assert _normalize_path("/api/achievements/5/") == "/api/achievements/{id}/"

    def test_playlist_id(self):
        assert _normalize_path("/api/playlists/123/") == "/api/playlists/{id}/"

    def test_no_match_unchanged(self):
        assert _normalize_path("/api/health/") == "/api/health/"
