"""Application Django pour les playlists."""
from django.apps import AppConfig


class PlaylistsConfig(AppConfig):
    """Configuration de l'application playlists."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.playlists"
    verbose_name = "Playlists"
