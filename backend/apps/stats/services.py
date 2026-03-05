"""Services de statistiques et leaderboards.

Factorise la logique métier partagée entre les vues stats et le viewset games.
"""

from __future__ import annotations

from apps.users.models import User


def _build_leaderboard_entry(idx: int, user: User, extra: dict | None = None) -> dict:
    """Construit une entrée de leaderboard pour un utilisateur."""
    team_membership = user.team_memberships.first()
    team_name = team_membership.team.name if team_membership else None

    entry = {
        "rank": idx,
        "user_id": user.id,
        "username": user.username,
        "avatar": user.avatar.url if user.avatar else None,
        "total_points": user.total_points,
        "total_games": user.total_games_played,
        "total_wins": user.total_wins,
        "win_rate": round(user.win_rate, 1),
        "team_name": team_name,
    }
    if extra:
        entry.update(extra)
    return entry


def get_global_leaderboard(offset: int, page_size: int) -> tuple[list[dict], int]:
    """Retourne le leaderboard global (hors superusers).

    Returns:
        tuple: (leaderboard_data, total_count)

    """
    users_qs = (
        User.objects.filter(total_games_played__gt=0)
        .exclude(is_superuser=True)
        .prefetch_related("team_memberships__team")
        .order_by("-total_points")
    )
    total_count = users_qs.count()
    users = users_qs[offset : offset + page_size]

    leaderboard = [
        _build_leaderboard_entry(idx, user)
        for idx, user in enumerate(users, offset + 1)
    ]

    return leaderboard, total_count
