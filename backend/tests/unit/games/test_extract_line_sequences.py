"""Tests unitaires de _extract_line_sequences."""

from apps.games.lyrics_service import _extract_line_sequences
from tests.base import BaseUnitTest


class TestExtractLineSequences(BaseUnitTest):
    """Vérifie l'extraction de séquences de mots dans les paroles."""

    def get_target_class(self):
        return _extract_line_sequences

    def test_single_word_sequence(self):
        result = _extract_line_sequences("Hello beautiful world tonight", 1)
        assert len(result) > 0
        for _start, seq in result:
            assert len(seq) == 1

    def test_two_word_sequences(self):
        result = _extract_line_sequences("Love changes everything around", 2)
        assert len(result) > 0
        for _start, seq in result:
            assert len(seq) == 2

    def test_boring_words_filtered(self):
        # "the" and "oh" are boring words — sequences containing them are excluded
        result = _extract_line_sequences("the oh yeah", 1)
        assert len(result) == 0

    def test_short_words_filtered(self):
        result = _extract_line_sequences("I x y", 1)
        # Words < 2 chars should be filtered
        assert all(len(seq[0]) >= 2 for _, seq in result)

    def test_empty_line(self):
        result = _extract_line_sequences("", 1)
        assert result == []

    def test_line_shorter_than_n(self):
        result = _extract_line_sequences("Hello", 3)
        assert result == []

    def test_returns_start_indices(self):
        result = _extract_line_sequences("beautiful wonderful amazing", 1)
        starts = [s for s, _ in result]
        # Indices should be sequential
        assert all(isinstance(s, int) for s in starts)
