"""Validateurs pour les fichiers uploadés (avatars, etc.)."""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

# Taille maximale en octets (5 Mo)
MAX_AVATAR_SIZE = 5 * 1024 * 1024

# Types MIME autorisés pour les avatars
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def validate_avatar(file):
    """Valide la taille et le type MIME d'un fichier avatar."""
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
            _(
                "Type de fichier non autorisé. Formats acceptés : JPEG, PNG, WebP, GIF."
            ),
            code="invalid_mime_type",
        )
