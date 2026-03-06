"""Signals for the games app.

Recalculates denormalized user stats from the source of truth
(GamePlayer records) instead of error-prone manual increments.
"""

from __future__ import annotations

import logging
from typing import Any

from django.db.models import Sum
from django.db.models.functions import Coalesce
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


@receiver(post_save, sender=Game)
def update_team_stats_on_game_finish(
    sender: type, instance: Game, **kwargs: Any
) -> None:
    """Recalculate team denormalized stats when a game finishes."""
    if instance.status != GameStatus.FINISHED:
        return

    from apps.users.models import Team

    # Collect all teams that have members in this game
    team_ids = set()
    for player in instance.players.select_related("user"):
        for tm in player.user.team_memberships.select_related("team").all():
            team_ids.add(tm.team_id)

    if not team_ids:
        return

    # Recalculate stats for each affected team from source of truth
    for team in Team.objects.filter(id__in=team_ids):
        aggregated = team.members.aggregate(
            sum_games=Coalesce(Sum("total_games_played"), 0),
            sum_wins=Coalesce(Sum("total_wins"), 0),
            sum_points=Coalesce(Sum("total_points"), 0),
        )
        team.total_games = aggregated["sum_games"]
        team.total_wins = aggregated["sum_wins"]
        team.total_points = aggregated["sum_points"]
        team.save(update_fields=["total_games", "total_wins", "total_points"])
