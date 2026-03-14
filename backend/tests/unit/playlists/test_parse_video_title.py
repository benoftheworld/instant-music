"""Tests unitaires de _parse_video_title."""

from apps.playlists.youtube_service import YouTubeService
from tests.base import BaseUnitTest


class TestParseVideoTitle(BaseUnitTest):
    """Vérifie le parsing de titres de vidéos YouTube."""

    def get_target_class(self):
        return YouTubeService._parse_video_title

    def test_standard_dash_separator(self):
        artist, track = YouTubeService._parse_video_title("Queen - Bohemian Rhapsody")
        assert artist == "Queen"
        assert track == "Bohemian Rhapsody"

    def test_en_dash_separator(self):
        artist, track = YouTubeService._parse_video_title("Adele – Hello")
        assert artist == "Adele"
        assert track == "Hello"

    def test_em_dash_separator(self):
        artist, track = YouTubeService._parse_video_title("Rihanna — Umbrella")
        assert artist == "Rihanna"
        assert track == "Umbrella"

    def test_pipe_separator(self):
        artist, track = YouTubeService._parse_video_title(
            "Pink Floyd | Comfortably Numb"
        )
        assert artist == "Pink Floyd"
        assert track == "Comfortably Numb"

    def test_double_slash_separator(self):
        artist, track = YouTubeService._parse_video_title("Artist // Track Name")
        assert artist == "Artist"
        assert track == "Track Name"

    def test_strips_official_video_suffix(self):
        artist, track = YouTubeService._parse_video_title(
            "Queen - Bohemian Rhapsody (Official Video)"
        )
        assert artist == "Queen"
        assert track == "Bohemian Rhapsody"

    def test_no_separator_returns_unknown_artist(self):
        artist, track = YouTubeService._parse_video_title("Just A Song Title")
        assert artist == "Artiste inconnu"
        assert "Just A Song Title" in track

    def test_inverted_order_suffix_before_separator(self):
        artist, track = YouTubeService._parse_video_title(
            "Song Title (Official Video) - Artist Name"
        )
        assert artist == "Song Title"
        assert track == "Artist Name"
