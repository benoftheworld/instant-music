"""Team model."""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from .user import User


class Team(models.Model):
    """Team for group play."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("nom"), max_length=100, unique=True)
    description = models.TextField(
        _("description"), max_length=500, blank=True
    )
    avatar = models.ImageField(
        _("avatar"),
        upload_to="team_avatars/",
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_teams",
        verbose_name=_("propriétaire"),
    )
    members = models.ManyToManyField(
        User,
        through="TeamMember",
        related_name="teams",
        verbose_name=_("membres"),
    )

    # Stats
    total_games = models.IntegerField(_("parties jouées"), default=0)
    total_wins = models.IntegerField(_("victoires"), default=0)
    total_points = models.IntegerField(_("points totaux"), default=0)

    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("modifié le"), auto_now=True)

    class Meta:
        verbose_name = _("équipe")
        verbose_name_plural = _("équipes")
        ordering = ["-total_points"]

    def __str__(self) -> str:
        return self.name  # type: ignore[no-any-return]
