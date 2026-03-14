"""Tests unitaires de parse_lrc."""

from apps.games.lyrics_service import parse_lrc
from tests.base import BaseUnitTest


class TestParseLrc(BaseUnitTest):
    """Vérifie le parsing de paroles au format LRC."""

    def get_target_class(self):
        return parse_lrc

    def test_empty_string_returns_empty(self):
        assert parse_lrc("") == []

    def test_single_line(self):
        result = parse_lrc("[01:23.45] Hello world")
        assert len(result) == 1
        assert result[0]["time_ms"] == 83450
        assert result[0]["text"] == "Hello world"

    def test_multiple_lines_sorted(self):
        lrc = "[00:30.00] Second line\n[00:10.00] First line"
        result = parse_lrc(lrc)
        assert len(result) == 2
        assert result[0]["time_ms"] < result[1]["time_ms"]
        assert result[0]["text"] == "First line"

    def test_centiseconds_two_digits(self):
        result = parse_lrc("[00:01.50] Test")
        assert result[0]["time_ms"] == 1500

    def test_milliseconds_three_digits(self):
        result = parse_lrc("[00:01.500] Test")
        assert result[0]["time_ms"] == 1500

    def test_empty_text_line_kept(self):
        result = parse_lrc("[00:05.00] ")
        assert len(result) == 1
        assert result[0]["text"] == ""

    def test_invalid_lines_ignored(self):
        lrc = "Not a timestamp\n[00:01.00] Valid\nAlso invalid"
        result = parse_lrc(lrc)
        assert len(result) == 1
        assert result[0]["text"] == "Valid"

    def test_zero_time(self):
        result = parse_lrc("[00:00.00] Start")
        assert result[0]["time_ms"] == 0
