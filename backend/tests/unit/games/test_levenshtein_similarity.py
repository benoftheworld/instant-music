"""Tests unitaires du calcul de similarité Levenshtein."""

from apps.games.services.text_matching import _levenshtein_similarity
from tests.base import BaseServiceUnitTest


class TestLevenshteinSimilarity(BaseServiceUnitTest):
    """Vérifie le calcul de similarité Levenshtein."""

    def get_service_module(self):
        import apps.games.services.text_matching

        return apps.games.services.text_matching

    def test_identical_strings(self):
        assert _levenshtein_similarity("hello", "hello") == 1.0

    def test_completely_different(self):
        sim = _levenshtein_similarity("abc", "xyz")
        assert sim < 0.5

    def test_empty_first(self):
        assert _levenshtein_similarity("", "hello") == 0.0

    def test_empty_second(self):
        assert _levenshtein_similarity("hello", "") == 0.0

    def test_both_empty(self):
        assert _levenshtein_similarity("", "") == 0.0

    def test_one_char_diff(self):
        sim = _levenshtein_similarity("hello", "hallo")
        assert sim > 0.7

    def test_long_strings_fallback(self):
        """Chaînes > 50 chars → fallback character-based."""
        g = "a" * 60
        c = "a" * 60
        assert _levenshtein_similarity(g, c) == 1.0
