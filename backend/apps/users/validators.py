"""Validateurs pour les fichiers uploadés (avatars, etc.)."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Taille maximale en octets (5 Mo)
MAX_AVATAR_SIZE = 5 * 1024 * 1024

# Types MIME autorisés pour les avatars
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

# Magic bytes pour la validation réelle du type de fichier
_MAGIC_BYTES = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",  # WebP begins with RIFF...WEBP
    b"GIF87a": "image/gif",
    b"GIF89a": "image/gif",
}


def _detect_image_type(file) -> str | None:
    """Détecte le type MIME réel via les magic bytes du fichier."""
    pos = file.tell()
    header = file.read(12)
    file.seek(pos)

    if not header:
        return None

    for magic, mime in _MAGIC_BYTES.items():
        if header.startswith(magic):
            # Vérification supplémentaire pour WebP (RIFF...WEBP)
            if magic == b"RIFF" and header[8:12] != b"WEBP":
                continue
            return mime
    return None


def validate_avatar(file):
    """Validate the size and MIME type of an avatar file."""
    # Vérification de la taille
    if file.size > MAX_AVATAR_SIZE:
        raise ValidationError(
            _("Le fichier est trop volumineux. Taille maximale : 5 Mo."),
            code="file_too_large",
        )

    # Vérification du type MIME via le content_type déclaré par le navigateur
    content_type = getattr(file, "content_type", None)
    if content_type and content_type not in ALLOWED_AVATAR_TYPES:
        raise ValidationError(
            _("Type de fichier non autorisé. Formats acceptés : JPEG, PNG, WebP, GIF."),
            code="invalid_file_type",
        )

    # Vérification des magic bytes (empêche l'envoi de fichiers malveillants
    # avec un content_type falsifié)
    real_type = _detect_image_type(file)
    if real_type is None or real_type not in ALLOWED_AVATAR_TYPES:
        raise ValidationError(
            _("Le contenu du fichier ne correspond pas à un format image autorisé."),
            code="invalid_file_content",
        )
