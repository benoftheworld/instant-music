"""Friendship model."""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from .enums import FriendshipStatus
from .user import User


class Friendship(models.Model):
    """Friendship between two users."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="friendships_sent",
        verbose_name=_("de l'utilisateur"),
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="friendships_received",
        verbose_name=_("à l'utilisateur"),
    )
    status = models.CharField(
        _("statut"),
        max_length=20,
        choices=FriendshipStatus.choices,
        default=FriendshipStatus.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("modifié le"), auto_now=True)

    class Meta:
        verbose_name = _("amitié")
        verbose_name_plural = _("amitiés")
        unique_together = ["from_user", "to_user"]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.from_user.username} → {self.to_user.username} ({self.status})"
