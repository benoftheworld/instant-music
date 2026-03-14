"""Models des succès et des succès débloqués par les utilisateurs."""

import uuid

from auditlog.registry import auditlog
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Achievement(models.Model):
    """Modèle de succès."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("nom"), max_length=100)
    description = models.TextField(_("description"))
    icon = models.ImageField(
        _("icône"), upload_to="achievements/", null=True, blank=True
    )
    points = models.IntegerField(_("points"), default=10)

    # Conditions
    condition_type = models.CharField(_("type de condition"), max_length=50)
    condition_value = models.IntegerField(_("valeur de condition"))
    condition_extra = models.CharField(
        _("contexte de condition"), max_length=100, null=True, blank=True
    )

    class Meta:
        """Meta options for the Achievement model."""

        verbose_name = _("succès")
        verbose_name_plural = _("succès")

    def __str__(self) -> str:
        """Affiche le nom de l'achievement."""
        return self.name  # type: ignore[no-any-return]


class UserAchievement(models.Model):
    """Succès débloqués par les utilisateurs."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="achievements",
    )
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(_("débloqué le"), auto_now_add=True)

    class Meta:
        """Options Meta pour le modèle UserAchievement."""

        verbose_name = _("succès utilisateur")
        verbose_name_plural = _("succès utilisateurs")
        unique_together = ["user", "achievement"]

    def __str__(self) -> str:
        """Affiche l'utilisateur et le succès débloqué."""
        return f"{self.user.username} - {self.achievement.name}"


auditlog.register(Achievement)
auditlog.register(UserAchievement)
