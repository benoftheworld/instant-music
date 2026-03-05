"""
Models for site-wide administration settings.

SiteConfiguration is a singleton — at most one row lives in the table.
Access it via SiteConfiguration.get_solo().
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError


class SiteConfiguration(models.Model):
    """
    Singleton model holding site-wide configuration.

    Only ONE row is allowed (pk=1 enforced in save/clean).
    Use ``SiteConfiguration.get_solo()`` to retrieve (or create) it.
    """

    # ── Maintenance ────────────────────────────────────────────────────────
    maintenance_mode = models.BooleanField(
        _("mode maintenance"),
        default=False,
        help_text=_(
            "Quand activé, toutes les requêtes non-admin retournent 503 "
            "et le frontend affiche le message de maintenance."
        ),
    )
    maintenance_title = models.CharField(
        _("titre de maintenance"),
        max_length=200,
        default="Maintenance en cours",
        blank=True,
        help_text=_("Titre affiché sur la page de maintenance."),
    )
    maintenance_message = models.TextField(
        _("message de maintenance"),
        default="Le site est temporairement indisponible pour maintenance. Merci de réessayer dans quelques instants.",
        blank=True,
        help_text=_(
            "Message affiché aux utilisateurs pendant la maintenance."
        ),
    )

    # ── Bandeau d'information ──────────────────────────────────────────────
    class BannerColor(models.TextChoices):
        INFO = "info", _("Bleu — information")
        SUCCESS = "success", _("Vert — succès")
        WARNING = "warning", _("Orange — avertissement")
        DANGER = "danger", _("Rouge — danger")

    banner_enabled = models.BooleanField(
        _("bandeau actif"),
        default=False,
        help_text=_("Affiche un bandeau en haut du frontend."),
    )
    banner_message = models.CharField(
        _("message du bandeau"),
        max_length=500,
        blank=True,
        default="",
        help_text=_("Texte affiché dans le bandeau (500 caractères max)."),
    )
    banner_color = models.CharField(
        _("couleur du bandeau"),
        max_length=10,
        choices=BannerColor.choices,
        default=BannerColor.INFO,
    )
    banner_dismissible = models.BooleanField(
        _("bandeau fermable"),
        default=True,
        help_text=_("L'utilisateur peut fermer le bandeau."),
    )

    # ── Metadata ──────────────────────────────────────────────────────────
    updated_at = models.DateTimeField(_("mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("Configuration du site")
        verbose_name_plural = _("Configuration du site")

    def __str__(self) -> str:
        status = "🔴 MAINTENANCE" if self.maintenance_mode else "🟢 En ligne"
        banner = " | 📢 Bandeau actif" if self.banner_enabled else ""
        return f"Configuration du site — {status}{banner}"

    def clean(self) -> None:
        """Only one SiteConfiguration row is allowed."""
        if self.pk and self.pk != 1:
            raise ValidationError(
                _("Il ne peut exister qu'une seule configuration du site.")
            )

    def save(self, *args, **kwargs) -> None:
        self.pk = 1  # Force singleton
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass  # Prevent deletion

    @classmethod
    def get_solo(cls) -> "SiteConfiguration":
        """Return the singleton instance, creating it with defaults if needed."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj  # type: ignore[no-any-return]


class LegalPage(models.Model):
    """
    Editable legal pages (privacy policy, legal notices).
    Each page_type can only exist once (unique constraint).
    """

    class PageType(models.TextChoices):
        PRIVACY = "privacy", _("Politique de confidentialité")
        LEGAL = "legal", _("Mentions légales")

    page_type = models.CharField(
        _("type de page"),
        max_length=20,
        choices=PageType.choices,
        unique=True,
    )
    title = models.CharField(_("titre"), max_length=200)
    content = models.TextField(
        _("contenu"),
        help_text=_(
            "Texte libre. Séparer les paragraphes par une ligne vide."
        ),
    )
    updated_at = models.DateTimeField(_("mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("Page légale")
        verbose_name_plural = _("Pages légales")

    def __str__(self) -> str:
        return self.get_page_type_display()  # type: ignore[no-any-return]


# Audit log — traçabilité des modifications admin
from auditlog.registry import auditlog

auditlog.register(SiteConfiguration)
auditlog.register(LegalPage)
