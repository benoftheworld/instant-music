"""Application Django pour les jeux."""
from django.apps import AppConfig


class GamesConfig(AppConfig):
    """Configuration de l'application games."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.games"
    verbose_name = "Games"

    def ready(self) -> None:
        """Register game signals when the app is ready."""
        import apps.games.signals  # noqa: F401
