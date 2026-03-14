"""Tests unitaires supplémentaires du YouTubeService (méthodes de service)."""

from unittest.mock import patch

from tests.base import BaseServiceUnitTest


class TestYouTubeServiceParseVideoTitle(BaseServiceUnitTest):
    """Vérifie _parse_video_title."""

    def get_service_module(self):
        from apps.playlists import youtube_service

        return youtube_service

    def test_standard_format(self):
        from apps.playlists.youtube_service import YouTubeService

        artist, title = YouTubeService._parse_video_title("Artist - Song Title")
        assert artist == "Artist"
        assert title == "Song Title"

    def test_official_video_suffix(self):
        from apps.playlists.youtube_service import YouTubeService

        artist, title = YouTubeService._parse_video_title(
            "Artist - Song Title (Official Video)"
        )
        assert artist == "Artist"
        assert "Official" not in title

    def test_no_separator(self):
        from apps.playlists.youtube_service import YouTubeService

        artist, title = YouTubeService._parse_video_title("Just a Title")
        assert artist == "Artiste inconnu"

    def test_en_dash_separator(self):
        from apps.playlists.youtube_service import YouTubeService

        artist, title = YouTubeService._parse_video_title("Artist – Song")
        assert artist == "Artist"
        assert title == "Song"

    def test_pipe_separator(self):
        from apps.playlists.youtube_service import YouTubeService

        artist, title = YouTubeService._parse_video_title("Artist | Song")
        assert artist == "Artist"
        assert title == "Song"


class TestYouTubeServiceParseIsoDuration(BaseServiceUnitTest):
    """Vérifie _parse_iso_duration."""

    def get_service_module(self):
        from apps.playlists import youtube_service

        return youtube_service

    def test_minutes_seconds(self):
        from apps.playlists.youtube_service import YouTubeService

        assert YouTubeService._parse_iso_duration("PT4M13S") == 253000

    def test_hours(self):
        from apps.playlists.youtube_service import YouTubeService

        assert YouTubeService._parse_iso_duration("PT1H2M3S") == 3723000

    def test_zero(self):
        from apps.playlists.youtube_service import YouTubeService

        assert YouTubeService._parse_iso_duration("PT0S") == 0

    def test_invalid(self):
        from apps.playlists.youtube_service import YouTubeService

        assert YouTubeService._parse_iso_duration("invalid") == 0


class TestYouTubeServiceSearchPlaylists(BaseServiceUnitTest):
    """Vérifie search_playlists."""

    def get_service_module(self):
        from apps.playlists import youtube_service

        return youtube_service

    @patch("apps.playlists.youtube_service.cache")
    def test_cached_result(self, mock_cache):
        mock_cache.get.return_value = [{"playlist_id": "p1"}]
        from apps.playlists.youtube_service import YouTubeService

        svc = YouTubeService()
        result = svc.search_playlists("test")
        assert len(result) == 1

    @patch("apps.playlists.youtube_service.cache")
    def test_api_call(self, mock_cache):
        mock_cache.get.return_value = None
        from apps.playlists.youtube_service import YouTubeService

        svc = YouTubeService()
        svc.api_key = "key"
        with patch.object(svc, "_make_request") as mock_req:
            mock_req.return_value = {
                "items": [
                    {
                        "id": {"playlistId": "PL123"},
                        "snippet": {
                            "title": "Test PL",
                            "description": "desc",
                            "channelTitle": "Channel",
                            "thumbnails": {"high": {"url": "http://thumb.jpg"}},
                        },
                    }
                ]
            }
            result = svc.search_playlists("test")
            assert len(result) == 1
            assert result[0]["name"] == "Test PL"

    @patch("apps.playlists.youtube_service.cache")
    def test_api_error_returns_empty(self, mock_cache):
        mock_cache.get.return_value = None
        from apps.playlists.youtube_service import YouTubeAPIError, YouTubeService

        svc = YouTubeService()
        svc.api_key = "key"
        with patch.object(svc, "_make_request", side_effect=YouTubeAPIError("fail")):
            result = svc.search_playlists("test")
            assert result == []


class TestYouTubeServiceGetPlaylist(BaseServiceUnitTest):
    """Vérifie get_playlist."""

    def get_service_module(self):
        from apps.playlists import youtube_service

        return youtube_service

    @patch("apps.playlists.youtube_service.cache")
    def test_cached(self, mock_cache):
        mock_cache.get.return_value = {"playlist_id": "p1"}
        from apps.playlists.youtube_service import YouTubeService

        svc = YouTubeService()
        result = svc.get_playlist("p1")
        assert result is not None

    @patch("apps.playlists.youtube_service.cache")
    def test_api_success(self, mock_cache):
        mock_cache.get.return_value = None
        from apps.playlists.youtube_service import YouTubeService

        svc = YouTubeService()
        svc.api_key = "key"
        with patch.object(svc, "_make_request") as mock_req:
            mock_req.return_value = {
                "items": [
                    {
                        "snippet": {
                            "title": "PL",
                            "description": "desc",
                            "channelTitle": "Ch",
                            "thumbnails": {},
                        },
                        "contentDetails": {"itemCount": 10},
                    }
                ]
            }
            result = svc.get_playlist("p1")
            assert result is not None
            assert result["name"] == "PL"

    @patch("apps.playlists.youtube_service.cache")
    def test_not_found(self, mock_cache):
        mock_cache.get.return_value = None
        from apps.playlists.youtube_service import YouTubeService

        svc = YouTubeService()
        svc.api_key = "key"
        with patch.object(svc, "_make_request", return_value={"items": []}):
            result = svc.get_playlist("p1")
            assert result is None


class TestYouTubeServiceSearchMusicVideos(BaseServiceUnitTest):
    """Vérifie search_music_videos."""

    def get_service_module(self):
        from apps.playlists import youtube_service

        return youtube_service

    @patch("apps.playlists.youtube_service.cache")
    def test_success(self, mock_cache):
        mock_cache.get.return_value = None
        from apps.playlists.youtube_service import YouTubeService

        svc = YouTubeService()
        svc.api_key = "key"
        with (
            patch.object(svc, "_make_request") as mock_req,
            patch.object(
                svc, "_get_video_details", return_value={"v1": {"duration_ms": 180000}}
            ),
        ):
            mock_req.return_value = {
                "items": [
                    {
                        "id": {"videoId": "v1"},
                        "snippet": {
                            "title": "Artist - Song",
                            "channelTitle": "Channel",
                            "thumbnails": {"high": {"url": "http://t.jpg"}},
                        },
                    }
                ]
            }
            result = svc.search_music_videos("test")
            assert len(result) == 1
            assert result[0]["name"] == "Song"


class TestYouTubeServiceGetPlaylistTracks(BaseServiceUnitTest):
    """Vérifie get_playlist_tracks."""

    def get_service_module(self):
        from apps.playlists import youtube_service

        return youtube_service

    @patch("apps.playlists.youtube_service.cache")
    def test_success(self, mock_cache):
        mock_cache.get.return_value = None
        from apps.playlists.youtube_service import YouTubeService

        svc = YouTubeService()
        svc.api_key = "key"
        with (
            patch.object(svc, "_make_request") as mock_req,
            patch.object(
                svc,
                "_get_video_details",
                return_value={"v1": {"duration_ms": 180000, "embeddable": True}},
            ),
        ):
            mock_req.return_value = {
                "items": [
                    {
                        "snippet": {
                            "title": "Artist - Song",
                            "videoOwnerChannelTitle": "Channel",
                            "thumbnails": {},
                        },
                        "contentDetails": {"videoId": "v1"},
                    }
                ],
            }
            result = svc.get_playlist_tracks("PL1", limit=10)
            assert len(result) == 1

    @patch("apps.playlists.youtube_service.cache")
    def test_skips_deleted_videos(self, mock_cache):
        mock_cache.get.return_value = None
        from apps.playlists.youtube_service import YouTubeService

        svc = YouTubeService()
        svc.api_key = "key"
        with (
            patch.object(svc, "_make_request") as mock_req,
            patch.object(
                svc,
                "_get_video_details",
                return_value={"v1": {"duration_ms": 0, "embeddable": True}},
            ),
        ):
            mock_req.return_value = {
                "items": [
                    {
                        "snippet": {"title": "Deleted video", "thumbnails": {}},
                        "contentDetails": {"videoId": "v1"},
                    }
                ],
            }
            result = svc.get_playlist_tracks("PL1")
            assert len(result) == 0

    @patch("apps.playlists.youtube_service.cache")
    def test_skips_non_embeddable(self, mock_cache):
        mock_cache.get.return_value = None
        from apps.playlists.youtube_service import YouTubeService

        svc = YouTubeService()
        svc.api_key = "key"
        with (
            patch.object(svc, "_make_request") as mock_req,
            patch.object(
                svc,
                "_get_video_details",
                return_value={"v1": {"duration_ms": 180000, "embeddable": False}},
            ),
        ):
            mock_req.return_value = {
                "items": [
                    {
                        "snippet": {
                            "title": "Artist - Song",
                            "thumbnails": {},
                        },
                        "contentDetails": {"videoId": "v1"},
                    }
                ],
            }
            result = svc.get_playlist_tracks("PL1")
            assert len(result) == 0


class TestExtractThumbnailUrl(BaseServiceUnitTest):
    """Vérifie _extract_thumbnail_url."""

    def get_service_module(self):
        from apps.playlists import youtube_service

        return youtube_service

    def test_high_priority(self):
        from apps.playlists.youtube_service import _extract_thumbnail_url

        snippet = {
            "thumbnails": {
                "high": {"url": "high.jpg"},
                "medium": {"url": "med.jpg"},
            }
        }
        assert _extract_thumbnail_url(snippet) == "high.jpg"

    def test_medium_fallback(self):
        from apps.playlists.youtube_service import _extract_thumbnail_url

        snippet = {"thumbnails": {"medium": {"url": "med.jpg"}}}
        assert _extract_thumbnail_url(snippet) == "med.jpg"

    def test_empty(self):
        from apps.playlists.youtube_service import _extract_thumbnail_url

        assert _extract_thumbnail_url({}) == ""


class TestGetVideoDetails(BaseServiceUnitTest):
    """Vérifie _get_video_details."""

    def get_service_module(self):
        from apps.playlists import youtube_service

        return youtube_service

    def test_batch_processing(self):
        from apps.playlists.youtube_service import YouTubeService

        svc = YouTubeService()
        svc.api_key = "key"
        with patch.object(svc, "_make_request") as mock_req:
            mock_req.return_value = {
                "items": [
                    {
                        "id": "v1",
                        "contentDetails": {"duration": "PT3M30S"},
                        "status": {"embeddable": True},
                    }
                ]
            }
            result = svc._get_video_details(["v1"])
            assert "v1" in result
            assert result["v1"]["duration_ms"] == 210000
