"""Configuration de l'application shop.
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ShopConfig(AppConfig):
    """Configuration de l'application boutique."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.shop"
    verbose_name = _("Boutique")
