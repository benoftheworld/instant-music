"""Tests unitaires de la correspondance floue multi-stratégies."""

from apps.games.services.text_matching import fuzzy_match
from tests.base import BaseServiceUnitTest


class TestFuzzyMatch(BaseServiceUnitTest):
    """Vérifie la correspondance floue multi-stratégies."""

    def get_service_module(self):
        import apps.games.services.text_matching
        return apps.games.services.text_matching

    # ── Correspondance exacte ───────────────────────────────────────

    def test_exact_match_after_normalize(self):
        is_match, factor = fuzzy_match("The Beatles", "the beatles")
        assert is_match is True
        assert factor == 1.0

    # ── Contenance ──────────────────────────────────────────────────

    def test_substring_match(self):
        is_match, factor = fuzzy_match("Beatles", "The Beatles")
        assert is_match is True
        assert factor >= 0.75

    def test_short_substring_rejected(self):
        """Sous-chaîne trop courte (ratio < 0.4) → rejeté en contenance."""
        is_match, _ = fuzzy_match("a", "abcdefghij")
        assert isinstance(is_match, bool)

    # ── Word-set overlap (Jaccard) ──────────────────────────────────

    def test_word_overlap_match(self):
        is_match, factor = fuzzy_match(
            "Bohemian Rhapsody Queen", "Queen Bohemian Rhapsody"
        )
        assert is_match is True

    # ── Levenshtein ─────────────────────────────────────────────────

    def test_minor_typo_matches(self):
        is_match, factor = fuzzy_match("Bohemian Rhapsodi", "Bohemian Rhapsody")
        assert is_match is True
        assert factor > 0.65

    def test_very_different_rejects(self):
        is_match, factor = fuzzy_match("zzzzz", "abcde")
        assert is_match is False

    # ── Cas limites ─────────────────────────────────────────────────

    def test_empty_given(self):
        is_match, factor = fuzzy_match("", "hello")
        assert is_match is False
        assert factor == 0.0

    def test_empty_correct(self):
        is_match, factor = fuzzy_match("hello", "")
        assert is_match is False
        assert factor == 0.0

    def test_both_empty(self):
        is_match, factor = fuzzy_match("", "")
        assert is_match is False
        assert factor == 0.0

    def test_custom_threshold(self):
        """Seuil strict → rejet de correspondances partielles."""
        is_match, _ = fuzzy_match("abc", "abd", threshold=0.99)
        assert is_match is False
