
"""Tests unitaires de DeezerService."""

from unittest.mock import patch

import pytest

from apps.playlists.deezer_service import DeezerAPIError, DeezerService
from tests.base import BaseUnitTest


class TestDeezerServiceMakeRequest(BaseUnitTest):
    """Vérifie les méthodes de DeezerService."""

    def get_target_class(self):
        return DeezerService

    def setup_method(self):
        self.service = DeezerService()

    @patch.object(DeezerService, "_get_json")
    def test_make_request_success(self, mock_get):
        mock_get.return_value = {"data": []}
        result = self.service._make_request("/search/playlist", {"q": "rock"})
        assert result == {"data": []}

    @patch.object(DeezerService, "_get_json")
    def test_make_request_api_error_in_body(self, mock_get):
        mock_get.return_value = {"error": {"message": "Quota exceeded"}}
        try:
            self.service._make_request("/search")
            pytest.fail("Expected DeezerAPIError")
        except DeezerAPIError as e:
            assert "Quota exceeded" in str(e)

    @patch.object(DeezerService, "_make_request")
    @patch("apps.playlists.deezer_service.cache")
    def test_search_playlists_returns_normalized(self, mock_cache, mock_req):
        mock_cache.get.return_value = None
        mock_req.return_value = {
            "data": [
                {
                    "id": 123,
                    "title": "Rock Classics",
                    "picture_medium": "http://img.jpg",
                    "nb_tracks": 50,
                    "user": {"name": "Editor"},
                    "link": "http://deezer.com/pl/123",
                }
            ]
        }
        result = self.service.search_playlists("rock")
        assert len(result) == 1
        assert result[0]["playlist_id"] == "123"
        assert result[0]["name"] == "Rock Classics"

    @patch.object(DeezerService, "_make_request")
    @patch("apps.playlists.deezer_service.cache")
    def test_search_playlists_cached(self, mock_cache, mock_req):
        mock_cache.get.return_value = [{"playlist_id": "cached"}]
        result = self.service.search_playlists("rock")
        assert result[0]["playlist_id"] == "cached"
        mock_req.assert_not_called()

    def test_parse_track_no_preview_returns_none(self):
        item = {"id": 1, "title": "Song", "preview": "", "artist": {}, "album": {}}
        result = self.service._parse_track(item)
        assert result is None

    def test_parse_track_with_preview(self):
        item = {
            "id": 1,
            "title": "Song",
            "preview": "http://preview.mp3",
            "artist": {"name": "Artist"},
            "album": {"title": "Album", "cover_medium": "http://cover.jpg"},
        }
        result = self.service._parse_track(item)
        assert result is not None
        assert result["preview_url"] == "http://preview.mp3"
        assert result["artists"] == ["Artist"]

    def test_search_music_videos_delegates(self):
        with patch.object(self.service, "search_tracks", return_value=[]) as mock:
            self.service.search_music_videos("query", 10)
            mock.assert_called_once_with("query", 10)
