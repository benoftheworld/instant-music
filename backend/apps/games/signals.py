"""
Signals for the games app.

Recalculates denormalized user stats from the source of truth
(GamePlayer records) instead of error-prone manual increments.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Game, GamePlayer, GameStatus

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Game)
def update_player_stats_on_game_finish(
    sender: type, instance: Game, **kwargs: Any
) -> None:
    """Recalculate every participant's denormalized stats when a game finishes."""
    if instance.status != GameStatus.FINISHED:
        return

    for player in instance.players.select_related("user"):
        user = player.user
        participations = GamePlayer.objects.filter(
            user=user, game__status=GameStatus.FINISHED
        )

        user.total_games_played = participations.count()
        user.total_wins = (
            participations.filter(rank=1).exclude(game__mode="karaoke").count()
        )
        user.total_points = participations.aggregate(s=Sum("score"))["s"] or 0
        user.save(update_fields=["total_games_played", "total_wins", "total_points"])
