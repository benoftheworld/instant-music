"""
GameAnswer model — player's answer in a round.
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from .game_player import GamePlayer
from .game_round import GameRound


class GameAnswer(models.Model):
    """Player's answer in a round."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    round = models.ForeignKey(
        GameRound,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("round"),
    )
    player = models.ForeignKey(
        GamePlayer,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("joueur"),
    )
    answer = models.CharField(_("réponse"), max_length=255)
    is_correct = models.BooleanField(_("correct"), default=False)
    points_earned = models.IntegerField(_("points gagnés"), default=0)
    response_time = models.FloatField(_("temps de réponse (secondes)"))
    answered_at = models.DateTimeField(_("répondu le"), auto_now_add=True)

    class Meta:
        verbose_name = _("réponse")
        verbose_name_plural = _("réponses")
        unique_together = ["round", "player"]

    def __str__(self) -> str:
        return f"{self.player.user.username} - Round {self.round.round_number}"
