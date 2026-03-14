"""Tests d'intégration des vues playlists (Deezer + YouTube)."""

from unittest.mock import patch

import pytest
from rest_framework import status

from tests.base import BaseAPIIntegrationTest


@pytest.mark.django_db
class TestPlaylistSearch(BaseAPIIntegrationTest):
    """Vérifie la recherche de playlists Deezer."""

    def get_base_url(self):
        return "/api/playlists/"

    def test_search_no_query(self, api_client):
        resp = api_client.get(f"{self.get_base_url()}search/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    @patch("apps.playlists.views.deezer_service")
    def test_search_success(self, mock_deezer, api_client):
        mock_deezer.search_playlists.return_value = [
            {
                "playlist_id": "1",
                "name": "Rock",
                "description": "",
                "image_url": "http://img",
                "total_tracks": 10,
                "owner": "User",
                "external_url": "http://deezer.com/1",
            }
        ]
        resp = api_client.get(f"{self.get_base_url()}search/?query=rock")
        self.assert_status(resp, status.HTTP_200_OK)
        assert "playlists" in resp.data

    @patch("apps.playlists.views.deezer_service")
    def test_search_with_limit(self, mock_deezer, api_client):
        mock_deezer.search_playlists.return_value = []
        resp = api_client.get(f"{self.get_base_url()}search/?query=test&limit=5")
        self.assert_status(resp, status.HTTP_200_OK)
        mock_deezer.search_playlists.assert_called_once_with("test", 5)


@pytest.mark.django_db
class TestPlaylistGet(BaseAPIIntegrationTest):
    """Vérifie la récupération d'une playlist Deezer."""

    def get_base_url(self):
        return "/api/playlists/"

    @patch("apps.playlists.views.deezer_service")
    def test_get_playlist_success(self, mock_deezer, api_client):
        mock_deezer.get_playlist.return_value = {
            "playlist_id": "123",
            "name": "Rock",
            "description": "",
            "image_url": "http://img",
            "total_tracks": 10,
            "owner": "User",
            "external_url": "http://deezer.com/123",
        }
        resp = api_client.get(f"{self.get_base_url()}123/")
        self.assert_status(resp, status.HTTP_200_OK)

    @patch("apps.playlists.views.deezer_service")
    def test_get_playlist_not_found(self, mock_deezer, api_client):
        mock_deezer.get_playlist.return_value = None
        resp = api_client.get(f"{self.get_base_url()}999999/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
class TestPlaylistTracks(BaseAPIIntegrationTest):
    """Vérifie la récupération des pistes d'une playlist."""

    def get_base_url(self):
        return "/api/playlists/"

    @patch("apps.playlists.views.deezer_service")
    def test_get_tracks_success(self, mock_deezer, api_client):
        mock_deezer.get_playlist_tracks.return_value = [
            {
                "id": 1,
                "title": "Song",
                "artist": {"name": "Artist"},
                "preview": "http://mp3",
            }
        ]
        resp = api_client.get(f"{self.get_base_url()}123/tracks/")
        self.assert_status(resp, status.HTTP_200_OK)


@pytest.mark.django_db
class TestPlaylistValidate(BaseAPIIntegrationTest):
    """Vérifie la validation d'accès à une playlist."""

    def get_base_url(self):
        return "/api/playlists/"

    @patch("apps.playlists.views.deezer_service")
    def test_validate_accessible(self, mock_deezer, api_client):
        mock_deezer.get_playlist_tracks.return_value = [{"id": 1}, {"id": 2}]
        resp = api_client.get(f"{self.get_base_url()}123/validate/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data["accessible"] is True
        assert resp.data["track_count"] == 2

    @patch("apps.playlists.views.deezer_service")
    def test_validate_not_accessible(self, mock_deezer, api_client):
        mock_deezer.get_playlist_tracks.side_effect = Exception("Playlist not found")
        resp = api_client.get(f"{self.get_base_url()}123/validate/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data["accessible"] is False


@pytest.mark.django_db
class TestYouTubeSearch(BaseAPIIntegrationTest):
    """Vérifie la recherche YouTube."""

    def get_base_url(self):
        return "/api/playlists/"

    def test_youtube_search_no_query(self, auth_client):
        resp = auth_client.get(f"{self.get_base_url()}youtube-songs/search/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_youtube_search_too_short(self, auth_client):
        resp = auth_client.get(f"{self.get_base_url()}youtube-songs/search/?query=a")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    @patch("apps.playlists.views.youtube_service")
    @patch("apps.playlists.views.EXTERNAL_API_REQUESTS_TOTAL")
    def test_youtube_search_success(self, mock_metric, mock_yt, auth_client):
        mock_yt.search_music_videos.return_value = [
            {"id": "abc", "title": "Song", "channel": "Artist"}
        ]
        resp = auth_client.get(
            f"{self.get_base_url()}youtube-songs/search/?query=rock music"
        )
        self.assert_status(resp, status.HTTP_200_OK)
        assert "tracks" in resp.data

    @patch("apps.playlists.views.youtube_service")
    @patch("apps.playlists.views.EXTERNAL_API_REQUESTS_TOTAL")
    def test_youtube_search_api_error(self, mock_metric, mock_yt, auth_client):
        from apps.playlists.youtube_service import YouTubeAPIError

        mock_yt.search_music_videos.side_effect = YouTubeAPIError("quota exceeded")
        resp = auth_client.get(
            f"{self.get_base_url()}youtube-songs/search/?query=rock music"
        )
        self.assert_status(resp, status.HTTP_503_SERVICE_UNAVAILABLE)
