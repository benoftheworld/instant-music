"""Tests unitaires du modèle KaraokeSong — introspection des champs."""

from unittest.mock import MagicMock

from apps.games.models import KaraokeSong
from tests.base import BaseModelUnitTest


class TestKaraokeSongModel(BaseModelUnitTest):
    """Vérifie les champs, contraintes et métadonnées du modèle KaraokeSong."""

    def get_model_class(self):
        return KaraokeSong

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champs texte ────────────────────────────────────────────────

    def test_title_max_length(self):
        self.assert_field_max_length(KaraokeSong, "title", 255)

    def test_artist_max_length(self):
        self.assert_field_max_length(KaraokeSong, "artist", 255)

    def test_youtube_video_id_max_length(self):
        self.assert_field_max_length(KaraokeSong, "youtube_video_id", 20)

    def test_youtube_video_id_unique(self):
        self.assert_field_unique(KaraokeSong, "youtube_video_id", True)

    # ── lrclib_id ───────────────────────────────────────────────────

    def test_lrclib_id_null(self):
        self.assert_field_null(KaraokeSong, "lrclib_id", True)

    def test_lrclib_id_blank(self):
        self.assert_field_blank(KaraokeSong, "lrclib_id", True)

    # ── album_image_url ─────────────────────────────────────────────

    def test_album_image_url_blank(self):
        self.assert_field_blank(KaraokeSong, "album_image_url", True)

    def test_album_image_url_max_length(self):
        self.assert_field_max_length(KaraokeSong, "album_image_url", 500)

    # ── duration_ms ─────────────────────────────────────────────────

    def test_duration_ms_default(self):
        self.assert_field_default(KaraokeSong, "duration_ms", 0)

    # ── is_active ───────────────────────────────────────────────────

    def test_is_active_default(self):
        self.assert_field_default(KaraokeSong, "is_active", True)

    # ── Timestamps ──────────────────────────────────────────────────

    def test_created_at_auto_now_add(self):
        field = KaraokeSong._meta.get_field("created_at")
        assert field.auto_now_add is True

    def test_updated_at_auto_now(self):
        field = KaraokeSong._meta.get_field("updated_at")
        assert field.auto_now is True

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name("morceau karaoké", "morceaux karaoké")

    def test_ordering(self):
        self.assert_ordering(KaraokeSong, ["artist", "title"])

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        song = MagicMock(spec=KaraokeSong)
        song.artist = "Daft Punk"
        song.title = "Get Lucky"
        result = KaraokeSong.__str__(song)
        assert "Daft Punk" in result
        assert "Get Lucky" in result
