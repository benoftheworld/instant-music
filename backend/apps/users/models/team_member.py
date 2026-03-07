"""TeamMember model."""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from .enums import TeamMemberRole
from .team import Team
from .user import User


class TeamMember(models.Model):
    """Team membership."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name=_("équipe"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="team_memberships",
        verbose_name=_("utilisateur"),
    )
    role = models.CharField(
        _("rôle"),
        max_length=20,
        choices=TeamMemberRole.choices,
        default=TeamMemberRole.MEMBER,
    )
    joined_at = models.DateTimeField(_("a rejoint le"), auto_now_add=True)

    class Meta:
        verbose_name = _("membre d'équipe")
        verbose_name_plural = _("membres d'équipe")
        unique_together = ["team", "user"]
        ordering = ["joined_at"]

    def __str__(self) -> str:
        return f"{self.user.username} ({self.team.name})"
