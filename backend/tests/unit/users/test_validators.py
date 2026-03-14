"""Tests unitaires du validateur d'avatar."""

import io
from unittest.mock import MagicMock

import pytest
from django.core.exceptions import ValidationError

from apps.users.validators import (
    ALLOWED_AVATAR_TYPES,
    MAX_AVATAR_SIZE,
    _detect_image_type,
    validate_avatar,
)
from tests.base import BaseServiceUnitTest


class TestValidateAvatar(BaseServiceUnitTest):
    """Vérifie les trois niveaux de validation : taille, MIME, magic bytes."""

    def get_service_module(self):
        import apps.users.validators
        return apps.users.validators

    # ── Constantes ──────────────────────────────────────────────────

    def test_max_size_is_5mb(self):
        assert MAX_AVATAR_SIZE == 5 * 1024 * 1024

    def test_allowed_types(self):
        assert ALLOWED_AVATAR_TYPES == {
            "image/jpeg",
            "image/png",
            "image/webp",
            "image/gif",
        }

    # ── Taille ──────────────────────────────────────────────────────

    def test_file_too_large_raises(self):
        f = MagicMock()
        f.size = MAX_AVATAR_SIZE + 1
        with pytest.raises(ValidationError, match="trop volumineux"):
            validate_avatar(f)

    def test_file_exact_limit_passes_size_check(self):
        """Fichier de taille exacte ne lève pas l'erreur de taille."""
        f = MagicMock()
        f.size = MAX_AVATAR_SIZE
        f.content_type = "image/png"
        # Magic bytes PNG valides
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 4
        buf = io.BytesIO(data)
        f.read = buf.read
        f.tell = buf.tell
        f.seek = buf.seek
        validate_avatar(f)  # ne lève pas

    # ── Content-type MIME ───────────────────────────────────────────

    def test_invalid_content_type_raises(self):
        f = MagicMock()
        f.size = 100
        f.content_type = "application/pdf"
        with pytest.raises(ValidationError, match="Type de fichier non autorisé"):
            validate_avatar(f)

    def test_no_content_type_skips_mime_check(self):
        """Si content_type absent, seul le magic bytes est vérifié."""
        f = MagicMock(spec=[])  # pas d'attrs
        f.size = 100
        # content_type absent → getattr retourne None
        assert not hasattr(f, "content_type")
        data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 4
        buf = io.BytesIO(data)
        f.read = buf.read
        f.tell = buf.tell
        f.seek = buf.seek
        validate_avatar(f)

    # ── Magic bytes ─────────────────────────────────────────────────

    def test_invalid_magic_bytes_raises(self):
        f = MagicMock()
        f.size = 100
        f.content_type = "image/png"
        buf = io.BytesIO(b"\x00\x00\x00\x00" * 3)
        f.read = buf.read
        f.tell = buf.tell
        f.seek = buf.seek
        with pytest.raises(ValidationError, match="contenu du fichier"):
            validate_avatar(f)

    def test_empty_file_raises(self):
        f = MagicMock()
        f.size = 100
        f.content_type = "image/jpeg"
        buf = io.BytesIO(b"")
        f.read = buf.read
        f.tell = buf.tell
        f.seek = buf.seek
        with pytest.raises(ValidationError, match="contenu du fichier"):
            validate_avatar(f)

    # ── _detect_image_type ──────────────────────────────────────────

    def test_detect_jpeg(self):
        buf = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 9)
        assert _detect_image_type(buf) == "image/jpeg"

    def test_detect_png(self):
        buf = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 4)
        assert _detect_image_type(buf) == "image/png"

    def test_detect_webp(self):
        buf = io.BytesIO(b"RIFF\x00\x00\x00\x00WEBP")
        assert _detect_image_type(buf) == "image/webp"

    def test_detect_gif87a(self):
        buf = io.BytesIO(b"GIF87a" + b"\x00" * 6)
        assert _detect_image_type(buf) == "image/gif"

    def test_detect_gif89a(self):
        buf = io.BytesIO(b"GIF89a" + b"\x00" * 6)
        assert _detect_image_type(buf) == "image/gif"

    def test_detect_riff_not_webp(self):
        """RIFF sans 'WEBP' ne doit pas matcher."""
        buf = io.BytesIO(b"RIFF\x00\x00\x00\x00AVII")
        assert _detect_image_type(buf) is None

    def test_detect_unknown_returns_none(self):
        buf = io.BytesIO(b"\x00\x01\x02\x03\x04\x05")
        assert _detect_image_type(buf) is None

    def test_detect_empty_returns_none(self):
        buf = io.BytesIO(b"")
        assert _detect_image_type(buf) is None

    def test_file_position_restored(self):
        """Vérifie que la position du fichier est restaurée après détection."""
        buf = io.BytesIO(b"\x89PNG\r\n\x1a\n" + b"\x00" * 4)
        buf.seek(5)
        _detect_image_type(buf)
        assert buf.tell() == 5
