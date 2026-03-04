"""Service de construction des résultats de partie.

Extrait et factorise la logique commune aux endpoints `results` et `results_pdf`
pour éliminer la duplication de code.
"""

from __future__ import annotations

from django.db.models import Prefetch

from .models import Game, GameAnswer, GameRound


def build_rounds_detail(game: Game) -> tuple[list[dict], dict[str, int]]:
    """Construit le détail des rounds avec les séries de victoires par joueur.

    Returns:
        tuple: (rounds_detail, player_streaks)
    """
    rounds = (
        GameRound.objects.filter(game=game)
        .prefetch_related(
            Prefetch(
                "answers",
                queryset=GameAnswer.objects.select_related(
                    "player__user"
                ).order_by("-points_earned"),
            )
        )
        .order_by("round_number")
    )

    rounds_detail: list[dict] = []
    player_streaks: dict[str, int] = {}

    for r in rounds:
        answers = []
        for ans in r.answers.all().order_by("answered_at"):
            username = ans.player.user.username
            curr = player_streaks.get(username, 0)
            if ans.is_correct:
                curr += 1
            else:
                curr = 0
            player_streaks[username] = curr

            answers.append(
                {
                    "username": username,
                    "answer": ans.answer,
                    "is_correct": ans.is_correct,
                    "points_earned": ans.points_earned,
                    "response_time": round(ans.response_time, 1),
                    "consecutive_correct": curr,
                    "streak_bonus": ans.streak_bonus,
                }
            )

        rounds_detail.append(
            {
                "round_number": r.round_number,
                "track_name": r.track_name,
                "artist_name": r.artist_name,
                "correct_answer": r.correct_answer,
                "track_id": r.track_id,
                "answers": answers,
            }
        )

    return rounds_detail, player_streaks


def build_rankings(game: Game) -> list[dict]:
    """Construit le classement des joueurs avec les informations d'équipe."""
    players = (
        game.players.order_by("-score")
        .select_related("user")
        .prefetch_related("user__team_memberships__team")
    )

    rankings = []
    for p in players:
        team_name = None
        try:
            tm = p.user.team_memberships.first()
            if tm and tm.team:
                team_name = tm.team.name
        except Exception:
            team_name = None

        rankings.append(
            {
                "username": p.user.username,
                "score": p.score,
                "rank": p.rank,
                "team_name": team_name,
            }
        )

    return rankings
