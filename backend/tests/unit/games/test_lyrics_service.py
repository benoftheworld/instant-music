"""Tests unitaires du lyrics_service."""

import ssl
import urllib.error
from unittest.mock import MagicMock, patch

from tests.base import BaseServiceUnitTest


class TestParseLrc(BaseServiceUnitTest):
    """Vérifie parse_lrc."""

    def get_service_module(self):
        from apps.games import lyrics_service

        return lyrics_service

    def test_basic_parsing(self):
        from apps.games.lyrics_service import parse_lrc

        lrc = "[00:15.30] Hello world\n[01:05.50] Second line"
        result = parse_lrc(lrc)
        assert len(result) == 2
        assert result[0]["time_ms"] == 15300
        assert result[0]["text"] == "Hello world"
        assert result[1]["time_ms"] == 65500

    def test_empty_lines_kept(self):
        from apps.games.lyrics_service import parse_lrc

        lrc = "[00:10.00]\n[00:20.00] Words"
        result = parse_lrc(lrc)
        assert len(result) == 2
        assert result[0]["text"] == ""

    def test_invalid_lines_ignored(self):
        from apps.games.lyrics_service import parse_lrc

        lrc = "Not a valid line\n[00:10.00] Valid"
        result = parse_lrc(lrc)
        assert len(result) == 1

    def test_sorted_by_time(self):
        from apps.games.lyrics_service import parse_lrc

        lrc = "[01:00.00] Second\n[00:30.00] First"
        result = parse_lrc(lrc)
        assert result[0]["text"] == "First"


class TestCleanArtistTitle(BaseServiceUnitTest):
    """Vérifie _clean_artist_title."""

    def get_service_module(self):
        from apps.games import lyrics_service

        return lyrics_service

    def test_strips_parentheses(self):
        from apps.games.lyrics_service import _clean_artist_title

        a, t = _clean_artist_title("Artist (feat. X)", "Song (Remix)")
        assert a == "Artist"
        assert t == "Song"

    def test_no_parentheses(self):
        from apps.games.lyrics_service import _clean_artist_title

        a, t = _clean_artist_title("Artist", "Song")
        assert a == "Artist"
        assert t == "Song"


class TestGetLyrics(BaseServiceUnitTest):
    """Vérifie get_lyrics avec cache, LRCLib et fallback."""

    def get_service_module(self):
        from apps.games import lyrics_service

        return lyrics_service

    @patch("apps.games.lyrics_service.cache")
    def test_cached_result(self, mock_cache):
        mock_cache.get.return_value = "Cached lyrics text"
        from apps.games.lyrics_service import get_lyrics

        result = get_lyrics("Artist", "Song")
        assert result == "Cached lyrics text"

    @patch("apps.games.lyrics_service.cache")
    def test_cached_none(self, mock_cache):
        mock_cache.get.return_value = "__NONE__"
        from apps.games.lyrics_service import get_lyrics

        result = get_lyrics("Artist", "Song")
        assert result is None

    @patch("apps.games.lyrics_service.requests.get")
    @patch("apps.games.lyrics_service._lrclib_request")
    @patch("apps.games.lyrics_service.cache")
    def test_lrclib_success(self, mock_cache, mock_lrclib, mock_req):
        mock_cache.get.return_value = None
        long_lyrics = "A" * 100
        mock_lrclib.return_value = {"plainLyrics": long_lyrics}
        from apps.games.lyrics_service import get_lyrics

        result = get_lyrics("Artist", "Song")
        assert result == long_lyrics

    @patch("apps.games.lyrics_service.requests.get")
    @patch("apps.games.lyrics_service._lrclib_request")
    @patch("apps.games.lyrics_service.cache")
    def test_lyrics_ovh_fallback(self, mock_cache, mock_lrclib, mock_req):
        mock_cache.get.return_value = None
        mock_lrclib.return_value = None
        long_lyrics = "B" * 100
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"lyrics": long_lyrics}
        mock_req.return_value = mock_resp
        from apps.games.lyrics_service import get_lyrics

        result = get_lyrics("Artist", "Song")
        assert result == long_lyrics

    @patch("apps.games.lyrics_service.requests.get")
    @patch("apps.games.lyrics_service._lrclib_request")
    @patch("apps.games.lyrics_service.cache")
    def test_all_fail_returns_none(self, mock_cache, mock_lrclib, mock_req):
        mock_cache.get.return_value = None
        mock_lrclib.return_value = None
        mock_req.side_effect = Exception("timeout")
        from apps.games.lyrics_service import get_lyrics

        result = get_lyrics("Artist", "Song")
        assert result is None


class TestGetSyncedLyrics(BaseServiceUnitTest):
    """Vérifie get_synced_lyrics."""

    def get_service_module(self):
        from apps.games import lyrics_service

        return lyrics_service

    @patch("apps.games.lyrics_service.cache")
    def test_cached_result(self, mock_cache):
        mock_cache.get.return_value = {
            "lines": [{"time_ms": 0, "text": "hi"}],
            "lrclib_id": 42,
        }
        from apps.games.lyrics_service import get_synced_lyrics

        lines, lid = get_synced_lyrics("Artist", "Song")
        assert lines is not None
        assert lid == 42

    @patch("apps.games.lyrics_service.cache")
    def test_cached_none(self, mock_cache):
        mock_cache.get.return_value = "__NONE__"
        from apps.games.lyrics_service import get_synced_lyrics

        lines, lid = get_synced_lyrics("Artist", "Song")
        assert lines is None
        assert lid is None

    @patch("apps.games.lyrics_service.cache")
    def test_cached_legacy_list(self, mock_cache):
        mock_cache.get.return_value = [{"time_ms": 0, "text": "hi"}]
        from apps.games.lyrics_service import get_synced_lyrics

        lines, lid = get_synced_lyrics("Artist", "Song")
        assert lines is not None
        assert lid is None

    @patch("apps.games.lyrics_service._lrclib_search")
    @patch("apps.games.lyrics_service._lrclib_request")
    @patch("apps.games.lyrics_service.cache")
    def test_exact_query_success(self, mock_cache, mock_lrclib, mock_search):
        mock_cache.get.return_value = None
        mock_lrclib.return_value = {
            "syncedLyrics": "[00:10.00] Hello world\n[00:20.00] Second line",
            "id": 99,
        }
        from apps.games.lyrics_service import get_synced_lyrics

        lines, lid = get_synced_lyrics("Artist", "Song")
        assert lines is not None
        assert lid == 99

    @patch("apps.games.lyrics_service._lrclib_search")
    @patch("apps.games.lyrics_service._lrclib_request")
    @patch("apps.games.lyrics_service.cache")
    def test_search_fallback(self, mock_cache, mock_lrclib, mock_search):
        mock_cache.get.return_value = None
        mock_lrclib.return_value = None
        mock_search.return_value = {
            "syncedLyrics": "[00:05.00] Found via search",
            "id": 50,
        }
        from apps.games.lyrics_service import get_synced_lyrics

        lines, lid = get_synced_lyrics("Artist", "Song")
        assert lines is not None
        assert lid == 50

    @patch("apps.games.lyrics_service._lrclib_search")
    @patch("apps.games.lyrics_service._lrclib_request")
    @patch("apps.games.lyrics_service.cache")
    def test_all_fail(self, mock_cache, mock_lrclib, mock_search):
        mock_cache.get.return_value = None
        mock_lrclib.return_value = None
        mock_search.return_value = None
        from apps.games.lyrics_service import get_synced_lyrics

        lines, lid = get_synced_lyrics("Artist", "Song")
        assert lines is None
        assert lid is None

    @patch("apps.games.lyrics_service._lrclib_search")
    @patch("apps.games.lyrics_service._lrclib_request")
    @patch("apps.games.lyrics_service.cache")
    def test_unknown_artist_skips_exact(self, mock_cache, mock_lrclib, mock_search):
        mock_cache.get.return_value = None
        mock_search.return_value = {
            "syncedLyrics": "[00:05.00] Line",
            "id": 10,
        }
        from apps.games.lyrics_service import get_synced_lyrics

        lines, lid = get_synced_lyrics("unknown artist", "Song Title")
        # Should NOT call _lrclib_request since artist is unknown placeholder
        mock_lrclib.assert_not_called()
        assert lines is not None


class TestGetSyncedLyricsByLrclibId(BaseServiceUnitTest):
    """Vérifie get_synced_lyrics_by_lrclib_id."""

    def get_service_module(self):
        from apps.games import lyrics_service

        return lyrics_service

    @patch("apps.games.lyrics_service.cache")
    def test_cached_result(self, mock_cache):
        mock_cache.get.return_value = [{"time_ms": 0, "text": "hi"}]
        from apps.games.lyrics_service import get_synced_lyrics_by_lrclib_id

        result = get_synced_lyrics_by_lrclib_id(42)
        assert result is not None

    @patch("apps.games.lyrics_service.cache")
    def test_cached_none(self, mock_cache):
        mock_cache.get.return_value = "__NONE__"
        from apps.games.lyrics_service import get_synced_lyrics_by_lrclib_id

        result = get_synced_lyrics_by_lrclib_id(42)
        assert result is None

    @patch("apps.games.lyrics_service._lrclib_fetch")
    @patch("apps.games.lyrics_service.cache")
    def test_fetches_and_parses(self, mock_cache, mock_fetch):
        mock_cache.get.return_value = None
        mock_fetch.return_value = {"syncedLyrics": "[00:10.00] Hello\n[00:20.00] World"}
        from apps.games.lyrics_service import get_synced_lyrics_by_lrclib_id

        result = get_synced_lyrics_by_lrclib_id(42)
        assert result is not None
        assert len(result) == 2

    @patch("apps.games.lyrics_service._lrclib_fetch")
    @patch("apps.games.lyrics_service.cache")
    def test_fetch_fails(self, mock_cache, mock_fetch):
        mock_cache.get.return_value = None
        mock_fetch.return_value = None
        from apps.games.lyrics_service import get_synced_lyrics_by_lrclib_id

        result = get_synced_lyrics_by_lrclib_id(42)
        assert result is None


class TestLrclibFetch(BaseServiceUnitTest):
    """Vérifie _lrclib_fetch et circuit breaker."""

    def get_service_module(self):
        from apps.games import lyrics_service

        return lyrics_service

    @patch("apps.games.lyrics_service.cache")
    def test_circuit_open_returns_none(self, mock_cache):
        mock_cache.get.return_value = True  # circuit is open
        from apps.games.lyrics_service import _lrclib_fetch

        result = _lrclib_fetch("https://lrclib.net/api/get")
        assert result is None

    @patch("apps.games.lyrics_service.urllib.request.urlopen")
    @patch("apps.games.lyrics_service._lrclib_is_down", return_value=False)
    def test_ssl_error_no_circuit_break(self, mock_down, mock_urlopen):
        mock_urlopen.side_effect = ssl.SSLError("handshake failed")
        from apps.games.lyrics_service import _lrclib_fetch

        result = _lrclib_fetch("https://lrclib.net/api/get")
        assert result is None

    @patch("apps.games.lyrics_service._lrclib_mark_down")
    @patch("apps.games.lyrics_service.urllib.request.urlopen")
    @patch("apps.games.lyrics_service._lrclib_is_down", return_value=False)
    def test_connection_error_opens_circuit(self, mock_down, mock_urlopen, mock_mark):
        mock_urlopen.side_effect = urllib.error.URLError("connection refused")
        from apps.games.lyrics_service import _lrclib_fetch

        result = _lrclib_fetch("https://lrclib.net/api/get")
        assert result is None
        mock_mark.assert_called_once()

    @patch("apps.games.lyrics_service.urllib.request.urlopen")
    @patch("apps.games.lyrics_service._lrclib_is_down", return_value=False)
    def test_timeout_error(self, mock_down, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError("timeout")
        from apps.games.lyrics_service import _lrclib_fetch

        result = _lrclib_fetch("https://lrclib.net/api/get")
        assert result is None

    @patch("apps.games.lyrics_service.urllib.request.urlopen")
    @patch("apps.games.lyrics_service._lrclib_is_down", return_value=False)
    def test_http_error(self, mock_down, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            "url",
            404,
            "Not Found",
            None,  # type: ignore[arg-type]
            None,
        )
        from apps.games.lyrics_service import _lrclib_fetch

        result = _lrclib_fetch("https://lrclib.net/api/get")
        assert result is None


class TestCreateLyricsQuestion(BaseServiceUnitTest):
    """Vérifie create_lyrics_question."""

    def get_service_module(self):
        from apps.games import lyrics_service

        return lyrics_service

    def test_success(self):
        from apps.games.lyrics_service import create_lyrics_question

        lyrics = "\n".join(
            [
                "This is the beautiful morning sunshine today",
                "Another wonderful evening moonlight forever shining",
                "Fantastic dreamlike journey through mountains valleys",
                "Running quickly between enormous ancient buildings",
                "Singing loudly underneath sparkling brilliant stars",
            ]
        )
        result = create_lyrics_question(lyrics, words_to_blank=1)
        assert result is not None
        snippet, correct, options = result
        assert "_____" in snippet
        assert correct in options
        assert len(options) == 4

    def test_empty_lyrics(self):
        from apps.games.lyrics_service import create_lyrics_question

        result = create_lyrics_question("", words_to_blank=1)
        assert result is None

    def test_short_lines_only(self):
        from apps.games.lyrics_service import create_lyrics_question

        result = create_lyrics_question("Hi\nYo\nOk", words_to_blank=1)
        assert result is None


class TestExtractLineSequences(BaseServiceUnitTest):
    """Vérifie _extract_line_sequences."""

    def get_service_module(self):
        from apps.games import lyrics_service

        return lyrics_service

    def test_extracts_valid_sequences(self):
        from apps.games.lyrics_service import _extract_line_sequences

        line = "wonderful evening moonlight forever shining"
        seqs = _extract_line_sequences(line, 1)
        assert len(seqs) > 0

    def test_boring_words_excluded(self):
        from apps.games.lyrics_service import _extract_line_sequences

        line = "the and for but"
        seqs = _extract_line_sequences(line, 1)
        assert len(seqs) == 0

    def test_short_words_excluded(self):
        from apps.games.lyrics_service import _extract_line_sequences

        line = "a b c d"
        seqs = _extract_line_sequences(line, 1)
        assert len(seqs) == 0


class TestLrclibSearch(BaseServiceUnitTest):
    """Vérifie _lrclib_search."""

    def get_service_module(self):
        from apps.games import lyrics_service

        return lyrics_service

    @patch("apps.games.lyrics_service._lrclib_fetch")
    def test_prefers_synced(self, mock_fetch):
        mock_fetch.return_value = [
            {"plainLyrics": "plain", "syncedLyrics": None},
            {"plainLyrics": "p2", "syncedLyrics": "[00:10.00] line"},
        ]
        from apps.games.lyrics_service import _lrclib_search

        result = _lrclib_search("query")
        assert result is not None
        assert result["syncedLyrics"] is not None

    @patch("apps.games.lyrics_service._lrclib_fetch")
    def test_returns_first_if_no_synced(self, mock_fetch):
        mock_fetch.return_value = [
            {"plainLyrics": "plain", "syncedLyrics": None},
        ]
        from apps.games.lyrics_service import _lrclib_search

        result = _lrclib_search("query")
        assert result is not None
        assert result["plainLyrics"] == "plain"

    @patch("apps.games.lyrics_service._lrclib_fetch")
    def test_empty_results(self, mock_fetch):
        mock_fetch.return_value = []
        from apps.games.lyrics_service import _lrclib_search

        result = _lrclib_search("query")
        assert result is None

    @patch("apps.games.lyrics_service._lrclib_fetch")
    def test_none_result(self, mock_fetch):
        mock_fetch.return_value = None
        from apps.games.lyrics_service import _lrclib_search

        result = _lrclib_search("query")
        assert result is None
