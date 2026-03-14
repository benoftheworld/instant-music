"""Tests unitaires de _extract_thumbnail_url."""

from apps.playlists.youtube_service import _extract_thumbnail_url
from tests.base import BaseUnitTest


class TestExtractThumbnailUrl(BaseUnitTest):
    """Vérifie l'extraction de l'URL de miniature."""

    def get_target_class(self):
        return _extract_thumbnail_url

    def test_prefers_high(self):
        snippet = {
            "thumbnails": {
                "default": {"url": "default.jpg"},
                "medium": {"url": "medium.jpg"},
                "high": {"url": "high.jpg"},
            }
        }
        assert _extract_thumbnail_url(snippet) == "high.jpg"

    def test_fallback_to_medium(self):
        snippet = {
            "thumbnails": {
                "default": {"url": "default.jpg"},
                "medium": {"url": "medium.jpg"},
            }
        }
        assert _extract_thumbnail_url(snippet) == "medium.jpg"

    def test_fallback_to_default(self):
        snippet = {"thumbnails": {"default": {"url": "default.jpg"}}}
        assert _extract_thumbnail_url(snippet) == "default.jpg"

    def test_empty_thumbnails(self):
        assert _extract_thumbnail_url({"thumbnails": {}}) == ""

    def test_no_thumbnails_key(self):
        assert _extract_thumbnail_url({}) == ""
