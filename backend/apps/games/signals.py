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

from django.db.models import Count as models_Count

from django.db.models import Q, Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Game, GamePlayer, GameStatus

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Game)
def update_player_stats_on_game_finish(
    sender: type, instance: Game, **kwargs: Any
) -> None:
    """Recalculate every participant's denormalized stats when a game finishes.

    Optimisé : une seule requête annotée au lieu de N requêtes par joueur.
    """
    if instance.status != GameStatus.FINISHED:
        return

    user_ids = list(
        instance.players.values_list("user_id", flat=True)
    )

    if not user_ids:
        return

    from django.contrib.auth import get_user_model

    User = get_user_model()

    # Agréger toutes les stats en une seule requête annotée par utilisateur
    stats = (
        GamePlayer.objects.filter(
            user_id__in=user_ids, game__status=GameStatus.FINISHED
        )
        .values("user_id")
        .annotate(
            _total_games=models_Count("id"),
            _total_wins=models_Count(
                "id", filter=Q(rank=1, game__is_online=True)
            ),
            _total_points=Sum(
                "score",
                filter=Q(game__is_online=True) | Q(game__mode="karaoke"),
                default=0,
            ),
        )
    )

    stats_map = {s["user_id"]: s for s in stats}

    for user in User.objects.filter(id__in=user_ids):
        s = stats_map.get(user.id, {})
        user.total_games_played = s.get("_total_games", 0)
        user.total_wins = s.get("_total_wins", 0)
        user.total_points = s.get("_total_points", 0)
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
    player_user_ids = list(instance.players.values_list("user_id", flat=True))

    from apps.users.models.team_member import TeamMember

    team_ids = set(
        TeamMember.objects.filter(user_id__in=player_user_ids)
        .values_list("team_id", flat=True)
    )

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
