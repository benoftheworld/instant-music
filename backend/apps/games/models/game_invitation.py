"""GameInvitation model."""

import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.users.models import User

from .game import Game


class InvitationStatus(models.TextChoices):
    """Statuts possibles d'une invitation de partie."""

    PENDING = "pending", _("En attente")
    ACCEPTED = "accepted", _("Acceptée")
    DECLINED = "declined", _("Refusée")
    EXPIRED = "expired", _("Expirée")
    CANCELLED = "cancelled", _("Annulée")


INVITATION_TTL_MINUTES = 30


class GameInvitation(models.Model):
    """Invitation envoyée par un joueur à un ami pour rejoindre sa partie."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="invitations",
        verbose_name=_("partie"),
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="sent_game_invitations",
        verbose_name=_("expéditeur"),
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_game_invitations",
        verbose_name=_("destinataire"),
    )
    status = models.CharField(
        _("statut"),
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(_("créée le"), auto_now_add=True)
    expires_at = models.DateTimeField(_("expire le"), db_index=True)

    class Meta:
        verbose_name = _("invitation de partie")
        verbose_name_plural = _("invitations de partie")
        ordering = ["-created_at"]
        # Un ami ne peut avoir qu'une invitation en attente par partie
        unique_together = ["game", "recipient"]

    def __str__(self) -> str:
        return (
            f"{self.sender.username} → {self.recipient.username} "
            f"({self.game.room_code}, {self.status})"
        )

    def save(self, *args, **kwargs):
        """Save the invitation, setting expires_at if not already provided."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=INVITATION_TTL_MINUTES)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        """Check whether the invitation has expired."""
        return timezone.now() > self.expires_at  # type: ignore[no-any-return]
