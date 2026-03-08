"""Signals for the games app.

Recalculates denormalized user stats from the source of truth
(GamePlayer records) instead of error-prone manual increments.

Règles métier :
- total_wins : exclut les parties solo (is_online=False)
- total_points : exclut les parties solo sauf karaoké
- Team stats : dédupliquées par partie (pas de double-comptage si
  deux membres de la même équipe jouent ensemble)
"""

from __future__ import annotations

import logging
from typing import Any

from django.db.models import Q, Sum
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
        # Victoires : uniquement les parties multijoueur (is_online=True)
        user.total_wins = participations.filter(
            rank=1, game__is_online=True
        ).count()
        # Points : exclure les parties solo sauf karaoké
        user.total_points = (
            participations.filter(
                Q(game__is_online=True) | Q(game__mode="karaoke")
            ).aggregate(s=Sum("score"))["s"]
            or 0
        )
        user.save(update_fields=["total_games_played", "total_wins", "total_points"])


@receiver(post_save, sender=Game)
def update_team_stats_on_game_finish(
    sender: type, instance: Game, **kwargs: Any
) -> None:
    """Recalculate team denormalized stats when a game finishes.

    Les stats d'équipe sont calculées à partir des participations GamePlayer
    (et non de la somme des stats dénormalisées des membres) afin d'éviter
    le double-comptage quand deux membres jouent dans la même partie.
    """
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

    for team in Team.objects.filter(id__in=team_ids):
        member_ids = set(team.members.values_list("id", flat=True))

        all_participations = GamePlayer.objects.filter(
            user_id__in=member_ids,
            game__status=GameStatus.FINISHED,
        )

        # Parties : nombre de parties distinctes avec au moins un membre
        team.total_games = (
            all_participations.values("game_id").distinct().count()
        )

        # Victoires : parties distinctes où un membre est 1er (hors solo)
        team.total_wins = (
            all_participations.filter(rank=1, game__is_online=True)
            .values("game_id")
            .distinct()
            .count()
        )

        # Points : somme des scores des membres (hors solo non-karaoké)
        team.total_points = (
            all_participations.filter(
                Q(game__is_online=True) | Q(game__mode="karaoke")
            ).aggregate(s=Sum("score"))["s"]
            or 0
        )

        team.save(update_fields=["total_games", "total_wins", "total_points"])
