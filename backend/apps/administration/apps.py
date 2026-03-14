"""App configuration for administration."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AdministrationConfig(AppConfig):
    """Config for the administration app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.administration"
    verbose_name = _("Administration du site")
