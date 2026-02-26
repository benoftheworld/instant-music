"""
GamePlayer model — players in a game.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from .game import Game


class GamePlayer(models.Model):
    """Players in a game."""

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
    is_connected = models.BooleanField(_("connecté"), default=True)
    joined_at = models.DateTimeField(_("a rejoint le"), auto_now_add=True)

    class Meta:
        verbose_name = _("joueur de partie")
        verbose_name_plural = _("joueurs de partie")
        unique_together = ["game", "user"]
        ordering = ["-score"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.game.room_code}"
