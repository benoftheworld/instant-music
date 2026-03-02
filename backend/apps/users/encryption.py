"""Utilitaires de chiffrement pour les données personnelles (RGPD)."""

import hashlib
import hmac

from cryptography.fernet import Fernet
from django.conf import settings


def get_fernet() -> Fernet:
    """Retourne une instance Fernet avec la clé de chiffrement configurée."""
    return Fernet(settings.EMAIL_ENCRYPTION_KEY.encode())


def encrypt_email(email: str) -> str:
    """Chiffre un email en clair et retourne le token chiffré (str)."""
    return get_fernet().encrypt(email.lower().encode()).decode()


def decrypt_email(token: str) -> str:
    """Déchiffre un token Fernet et retourne l'email en clair."""
    return get_fernet().decrypt(token.encode()).decode()


def hash_email(email: str) -> str:
    """
    Calcule un HMAC-SHA256 de l'email (normalisé en minuscules).

    Ce hash est utilisé pour les lookups ORM (WHERE email_hash = ?)
    sans nécessiter de déchiffrement. Sans la clé EMAIL_HASH_KEY,
    un attaquant ne peut pas reconstruire les emails par force brute.
    """
    return hmac.new(
        settings.EMAIL_HASH_KEY.encode(),
        email.lower().encode(),
        hashlib.sha256,
    ).hexdigest()
