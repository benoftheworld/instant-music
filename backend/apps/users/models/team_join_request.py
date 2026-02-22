"""TeamJoinRequest model."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .enums import TeamJoinRequestStatus
from .team import Team
from .user import User


class TeamJoinRequest(models.Model):
    """Request to join a team, approved by owner/admin only."""

    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="join_requests",
        verbose_name=_("équipe"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="team_join_requests",
        verbose_name=_("utilisateur"),
    )
    status = models.CharField(
        _("statut"),
        max_length=20,
        choices=TeamJoinRequestStatus.choices,
        default=TeamJoinRequestStatus.PENDING,
    )
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("modifié le"), auto_now=True)

    class Meta:
        verbose_name = _("demande d'adhésion")
        verbose_name_plural = _("demandes d'adhésion")
        unique_together = ["team", "user"]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user.username} → {self.team.name} ({self.status})"
