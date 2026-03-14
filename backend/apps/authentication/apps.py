"""Application Django pour l'authentification."""

from django.apps import AppConfig


class AuthenticationConfig(AppConfig):
    """Configuration de l'application authentication."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.authentication"
    verbose_name = "Authentication"
