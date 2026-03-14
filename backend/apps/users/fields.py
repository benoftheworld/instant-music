"""Champ Django pour stocker les emails chiffrés en base de données."""

import logging

from django import forms
from django.db import models

from .encryption import decrypt_email, encrypt_email

logger = logging.getLogger(__name__)


class EncryptedEmailField(models.TextField):
    """Représente un champ d'email chiffré en base de données.

    Ce champ utilise Fernet (AES-128) pour chiffrer les emails avant de les
    stocker en base de données. Le chiffrement est transparent pour les
    développeurs : ils peuvent lire et écrire des emails en clair, et le champ
    s'occupe du chiffrement/déchiffrement.
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
            # 1. Email non encore chiffré (migration en cours)
            # 2. EMAIL_ENCRYPTION_KEY différente de celle utilisée à l'écriture
            #    → vérifier que la clé dans .env correspond à celle du
            #    déploiement
            if value.startswith("gAAAAA"):
                # Token Fernet valide mais mauvaise clé → problème de config
                logger.error(
                    "Impossible de déchiffrer l'email (token Fernet détecté). "
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
