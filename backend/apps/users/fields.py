"""Champ Django pour stocker les emails chiffrés en base de données."""

import logging

from django import forms
from django.db import models

from .encryption import decrypt_email, encrypt_email

logger = logging.getLogger(__name__)


class EncryptedEmailField(models.TextField):
    """Champ qui chiffre automatiquement l'email à l'écriture (Fernet/AES)
    et le déchiffre à la lecture.

    En base de données : token chiffré opaque (ex: gAAAAA...)
    En Python          : email en clair   (ex: user@example.com)
    """

    description = "Email chiffré (Fernet AES-128)"

    def from_db_value(self, value, expression, connection):  # noqa: ARG002
        """Déchiffre la valeur lue depuis la base de données."""
        if value is None:
            return value
        try:
            return decrypt_email(value)
        except Exception:
            # Deux causes possibles :
            # 1. Email non encore chiffré (migration en cours) — retourner tel quel
            # 2. EMAIL_ENCRYPTION_KEY différente de celle utilisée à l'écriture
            #    → vérifier que la clé dans .env correspond à celle du déploiement
            if value.startswith("gAAAAA"):
                # Token Fernet valide mais mauvaise clé → problème de configuration
                logger.error(
                    "Impossible de déchiffrer un email (token Fernet détecté). "
                    "Vérifiez que EMAIL_ENCRYPTION_KEY est identique à la clé "
                    "utilisée lors de l'écriture en base de données."
                )
            return value

    def get_prep_value(self, value):
        """Chiffre la valeur avant écriture en base de données."""
        if value is None:
            return value
        # Si la valeur est déjà un token Fernet (migration), ne pas re-chiffrer
        if isinstance(value, str) and value.startswith("gAAAAA"):
            return value
        return encrypt_email(value)

    def formfield(self, **kwargs):
        """Utilise un EmailField standard dans les formulaires Django admin."""
        defaults = {"form_class": forms.EmailField}
        defaults.update(kwargs)
        return super().formfield(**defaults)
