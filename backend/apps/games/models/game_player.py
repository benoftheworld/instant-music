"""
GamePlayer model — players in a game.
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .game import Game


class GamePlayer(models.Model):
    """Players in a game."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="players",
        verbose_name=_("partie"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_participations",
        verbose_name=_("joueur"),
    )
    score = models.IntegerField(_("score"), default=0)
    rank = models.IntegerField(_("classement"), null=True, blank=True)
    consecutive_correct = models.IntegerField(
        _("série en cours"),
        default=0,
        help_text="Nombre de bonnes réponses consécutives dans la partie",
    )
    is_connected = models.BooleanField(
        _("connecté"), default=True, db_index=True
    )
    joined_at = models.DateTimeField(_("a rejoint le"), auto_now_add=True)

    class Meta:
        verbose_name = _("joueur de partie")
        verbose_name_plural = _("joueurs de partie")
        unique_together = ["game", "user"]
        ordering = ["-score"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.game.room_code}"
