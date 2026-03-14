"""Tests unitaires des méthodes du DeezerService."""

from unittest.mock import patch

from tests.base import BaseServiceUnitTest


class TestDeezerParseTrack(BaseServiceUnitTest):
    """Vérifie le parsing des tracks Deezer."""

    def get_service_module(self):
        import apps.playlists.deezer_service

        return apps.playlists.deezer_service

    def test_parses_valid_track(self):
        from apps.playlists.deezer_service import DeezerService

        svc = DeezerService()
        item = {
            "id": 12345,
            "title": "Test Song",
            "preview": "https://preview.url/mp3",
            "artist": {"name": "TestArtist"},
            "album": {"title": "TestAlbum", "cover_medium": "https://cover.url"},
            "duration": 30,
            "link": "https://deezer.com/track/12345",
        }
        result = svc._parse_track(item)
        assert result is not None
        assert result["track_id"] == "12345"
        assert result["name"] == "Test Song"
        assert result["artists"] == ["TestArtist"]
        assert result["preview_url"] == "https://preview.url/mp3"
        assert result["duration_ms"] == 30000

    def test_returns_none_without_preview(self):
        from apps.playlists.deezer_service import DeezerService

        svc = DeezerService()
        item = {"id": 12345, "title": "Test", "preview": "", "artist": {}, "album": {}}
        assert svc._parse_track(item) is None


class TestDeezerMakeRequest(BaseServiceUnitTest):
    """Vérifie _make_request."""

    def get_service_module(self):
        import apps.playlists.deezer_service

        return apps.playlists.deezer_service

    def test_success(self):
        from apps.playlists.deezer_service import DeezerService

        svc = DeezerService()
        with patch.object(svc, "_get_json", return_value={"data": [{"id": 1}]}):
            result = svc._make_request("/test")
        assert "data" in result

    def test_api_error(self):
        import pytest

        from apps.playlists.deezer_service import DeezerAPIError, DeezerService

        svc = DeezerService()
        with patch.object(
            svc, "_get_json", return_value={"error": {"message": "Bad request"}}
        ), pytest.raises(DeezerAPIError, match="Bad request"):
            svc._make_request("/test")


class TestDeezerSearchPlaylists(BaseServiceUnitTest):
    """Vérifie search_playlists."""

    def get_service_module(self):
        import apps.playlists.deezer_service

        return apps.playlists.deezer_service

    @patch("django.core.cache.cache.get", return_value=None)
    @patch("django.core.cache.cache.set")
    def test_returns_playlists(self, mock_set, mock_get):
        from apps.playlists.deezer_service import DeezerService

        svc = DeezerService()
        with patch.object(
            svc,
            "_make_request",
            return_value={
                "data": [
                    {
                        "id": 1,
                        "title": "Rock Hits",
                        "picture_medium": "https://img.url",
                        "nb_tracks": 50,
                        "user": {"name": "Editor"},
                        "link": "https://deezer.com/playlist/1",
                    }
                ]
            },
        ):
            result = svc.search_playlists("rock")
        assert len(result) == 1
        assert result[0]["name"] == "Rock Hits"
        assert result[0]["playlist_id"] == "1"

    @patch("django.core.cache.cache.get", return_value=[{"cached": True}])
    def test_returns_cached(self, mock_get):
        from apps.playlists.deezer_service import DeezerService

        svc = DeezerService()
        result = svc.search_playlists("rock")
        assert result == [{"cached": True}]


class TestDeezerGetPlaylist(BaseServiceUnitTest):
    """Vérifie get_playlist."""

    def get_service_module(self):
        import apps.playlists.deezer_service

        return apps.playlists.deezer_service

    @patch("django.core.cache.cache.get", return_value=None)
    @patch("django.core.cache.cache.set")
    def test_success(self, mock_set, mock_get):
        from apps.playlists.deezer_service import DeezerService

        svc = DeezerService()
        with patch.object(
            svc,
            "_make_request",
            return_value={
                "id": 1,
                "title": "My Playlist",
                "description": "Desc",
                "picture_medium": "https://img.url",
                "nb_tracks": 10,
                "creator": {"name": "Owner"},
                "link": "https://deezer.com/playlist/1",
            },
        ):
            result = svc.get_playlist("1")
        assert result is not None
        assert result["name"] == "My Playlist"

    @patch("django.core.cache.cache.get", return_value=None)
    def test_returns_none_on_error(self, mock_get):
        from apps.playlists.deezer_service import DeezerAPIError, DeezerService

        svc = DeezerService()
        with patch.object(
            svc, "_make_request", side_effect=DeezerAPIError("Not found")
        ):
            result = svc.get_playlist("999")
        assert result is None


class TestDeezerSearchTracks(BaseServiceUnitTest):
    """Vérifie search_tracks."""

    def get_service_module(self):
        import apps.playlists.deezer_service

        return apps.playlists.deezer_service

    @patch("django.core.cache.cache.get", return_value=None)
    @patch("django.core.cache.cache.set")
    def test_filters_no_preview(self, mock_set, mock_get):
        from apps.playlists.deezer_service import DeezerService

        svc = DeezerService()
        with patch.object(
            svc,
            "_make_request",
            return_value={
                "data": [
                    {
                        "id": 1,
                        "title": "Song",
                        "preview": "https://p.url",
                        "artist": {"name": "A"},
                        "album": {"title": "B"},
                        "duration": 30,
                    },
                    {
                        "id": 2,
                        "title": "No Preview",
                        "preview": "",
                        "artist": {"name": "C"},
                        "album": {"title": "D"},
                    },
                ]
            },
        ):
            result = svc.search_tracks("query")
        assert len(result) == 1


class TestDeezerGetTrackDetails(BaseServiceUnitTest):
    """Vérifie get_track_details."""

    def get_service_module(self):
        import apps.playlists.deezer_service

        return apps.playlists.deezer_service

    @patch("django.core.cache.cache.get", return_value=None)
    @patch("django.core.cache.cache.set")
    def test_success(self, mock_set, mock_get):
        from apps.playlists.deezer_service import DeezerService

        svc = DeezerService()
        with patch.object(
            svc,
            "_make_request",
            return_value={
                "id": 1,
                "title": "Track",
                "preview": "https://p.url",
                "artist": {"name": "A"},
                "album": {"title": "B"},
                "duration": 30,
                "release_date": "2023-01-01",
            },
        ):
            result = svc.get_track_details("1")
        assert result is not None
        assert result["release_date"] == "2023-01-01"

    @patch("django.core.cache.cache.get", return_value=None)
    def test_returns_none_on_error(self, mock_get):
        from apps.playlists.deezer_service import DeezerAPIError, DeezerService

        svc = DeezerService()
        with patch.object(svc, "_make_request", side_effect=DeezerAPIError("err")):
            result = svc.get_track_details("999")
        assert result is None


class TestDeezerSearchMusicVideos(BaseServiceUnitTest):
    """Vérifie search_music_videos alias."""

    def get_service_module(self):
        import apps.playlists.deezer_service

        return apps.playlists.deezer_service

    def test_delegates_to_search_tracks(self):
        from apps.playlists.deezer_service import DeezerService

        svc = DeezerService()
        with patch.object(
            svc, "search_tracks", return_value=[{"track": True}]
        ) as mock_st:
            result = svc.search_music_videos("query", 10)
            mock_st.assert_called_once_with("query", 10)
        assert result == [{"track": True}]


class TestDeezerGetPlaylistTracks(BaseServiceUnitTest):
    """Vérifie get_playlist_tracks."""

    def get_service_module(self):
        import apps.playlists.deezer_service

        return apps.playlists.deezer_service

    @patch("django.core.cache.cache.get", return_value=None)
    @patch("django.core.cache.cache.set")
    def test_fetches_and_parses(self, mock_set, mock_get):
        from apps.playlists.deezer_service import DeezerService

        svc = DeezerService()
        with patch.object(
            svc,
            "_make_request",
            return_value={
                "data": [
                    {
                        "id": 1,
                        "title": "Song",
                        "preview": "https://p.url",
                        "artist": {"name": "A"},
                        "album": {"title": "B"},
                        "duration": 30,
                    },
                ]
            },
        ):
            result = svc.get_playlist_tracks("123", limit=10)
        assert len(result) == 1

    @patch("django.core.cache.cache.get", return_value=[{"cached": True}])
    def test_returns_cached(self, mock_get):
        from apps.playlists.deezer_service import DeezerService

        svc = DeezerService()
        result = svc.get_playlist_tracks("123")
        assert result == [{"cached": True}]

    @patch("django.core.cache.cache.get", return_value=None)
    def test_raises_on_empty_first_page(self, mock_get):
        import pytest

        from apps.playlists.deezer_service import DeezerAPIError, DeezerService

        svc = DeezerService()
        with (
            patch.object(
                svc, "_make_request", side_effect=DeezerAPIError("err")
            ),
            pytest.raises(DeezerAPIError),
        ):
            svc.get_playlist_tracks("123")
