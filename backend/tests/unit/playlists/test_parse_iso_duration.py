"""Tests unitaires de _parse_iso_duration et _parse_video_title."""

from apps.playlists.youtube_service import YouTubeService
from tests.base import BaseUnitTest


class TestParseIsoDuration(BaseUnitTest):
    """Vérifie le parsing de durées ISO 8601."""

    def get_target_class(self):
        return YouTubeService._parse_iso_duration

    def test_minutes_and_seconds(self):
        assert YouTubeService._parse_iso_duration("PT4M13S") == 253000

    def test_hours_minutes_seconds(self):
        assert YouTubeService._parse_iso_duration("PT1H2M3S") == 3723000

    def test_seconds_only(self):
        assert YouTubeService._parse_iso_duration("PT30S") == 30000

    def test_minutes_only(self):
        assert YouTubeService._parse_iso_duration("PT5M") == 300000

    def test_hours_only(self):
        assert YouTubeService._parse_iso_duration("PT2H") == 7200000

    def test_invalid_format(self):
        assert YouTubeService._parse_iso_duration("invalid") == 0

    def test_empty_string(self):
        assert YouTubeService._parse_iso_duration("") == 0
