"""Tests unitaires du module text_matching."""

from apps.games.services.text_matching import normalize_text
from tests.base import BaseServiceUnitTest


class TestNormalizeText(BaseServiceUnitTest):
    """Vérifie la normalisation de texte pour la comparaison floue."""

    def get_service_module(self):
        import apps.games.services.text_matching

        return apps.games.services.text_matching

    def test_lowercase(self):
        assert normalize_text("HELLO") == "hello"

    def test_strip_whitespace(self):
        assert normalize_text("  hello  ") == "hello"

    def test_remove_accents(self):
        assert normalize_text("café") == "cafe"
        assert normalize_text("über") == "uber"
        assert normalize_text("résumé") == "resume"

    def test_remove_article_the(self):
        assert normalize_text("The Beatles") == "beatles"

    def test_remove_article_le(self):
        assert normalize_text("Le monde") == "monde"

    def test_remove_article_la(self):
        assert normalize_text("La vie") == "vie"

    def test_remove_article_les(self):
        assert normalize_text("Les fleurs") == "fleurs"

    def test_remove_article_l_apostrophe(self):
        assert normalize_text("L'amour") == "amour"

    def test_remove_article_un(self):
        assert normalize_text("Un jour") == "jour"

    def test_remove_article_une(self):
        assert normalize_text("Une chanson") == "chanson"

    def test_remove_article_des(self):
        assert normalize_text("Des roses") == "roses"

    def test_remove_punctuation(self):
        assert normalize_text("rock'n'roll!") == "rocknroll"

    def test_collapse_whitespace(self):
        assert normalize_text("hello   world") == "hello world"

    def test_combined(self):
        result = normalize_text("  L'Été Indien!  ")
        assert result == "ete indien"

    def test_empty_string(self):
        assert normalize_text("") == ""
