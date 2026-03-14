"""Tests unitaires de clean_track_title."""

from apps.playlists.deezer_service import clean_track_title
from tests.base import BaseUnitTest


class TestCleanTrackTitle(BaseUnitTest):
    """Vérifie le nettoyage des suffixes de titres de piste."""

    def get_target_class(self):
        return clean_track_title

    def test_remastered_parenthesised(self):
        assert clean_track_title("Bohemian Rhapsody (Remastered 2011)") == "Bohemian Rhapsody"

    def test_remastered_no_year(self):
        assert clean_track_title("Hymne à l'amour (Remastered)") == "Hymne à l'amour"

    def test_remastered_dash(self):
        assert clean_track_title("Hymne à l'amour - 2020 Remaster") == "Hymne à l'amour"

    def test_year_before_keyword(self):
        assert clean_track_title("Hotel California (2013 Remaster)") == "Hotel California"

    def test_french_variant(self):
        assert clean_track_title("Ma Benz [Remasterisée]") == "Ma Benz"

    def test_deluxe_edition(self):
        assert clean_track_title("Thriller (Deluxe Edition)") == "Thriller"

    def test_special_edition(self):
        assert clean_track_title("Album (Special Edition)") == "Album"

    def test_anniversary(self):
        assert clean_track_title("Song (Anniversary Edition)") == "Song"

    def test_dash_remastered(self):
        assert clean_track_title("Song - Remastered") == "Song"

    def test_unchanged_live(self):
        assert clean_track_title("Starman (Live)") == "Starman (Live)"

    def test_unchanged_no_suffix(self):
        assert clean_track_title("Emmenez-moi") == "Emmenez-moi"

    def test_unchanged_numbers(self):
        assert clean_track_title("99 Problems") == "99 Problems"

    def test_empty_returns_original(self):
        assert clean_track_title("") == ""
