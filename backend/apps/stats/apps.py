"""Application Django pour les statistiques."""
from django.apps import AppConfig


class StatsConfig(AppConfig):
    """Configuration de l'application stats."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.stats"
    verbose_name = "Statistics"
