"""Views for stats.
"""

import logging

from django.db.models import Avg, Count, Max, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.achievements.models import Achievement, UserAchievement
from apps.core.pagination import paginated_response, parse_pagination_params
from apps.core.throttles import LeaderboardThrottle
from apps.games.models import GameAnswer, GameMode, GamePlayer
from apps.users.models import Team, User

from .serializers import UserDetailedStatsSerializer
from .services import _build_leaderboard_entry, get_global_leaderboard

logger = logging.getLogger("apps.stats.views")


class UserDetailedStatsView(APIView):
    """Get detailed statistics for the current user."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Game stats from GamePlayer records
        game_players = GamePlayer.objects.filter(user=user, rank__isnull=False)
        total_games = game_players.count()
        total_wins = game_players.filter(rank=1).count()
        total_points = game_players.aggregate(s=Sum("score"))["s"] or 0
        best_score = game_players.aggregate(m=Max("score"))["m"] or 0
        avg_score = game_players.aggregate(a=Avg("score"))["a"] or 0.0

        # Answer stats
        answers = GameAnswer.objects.filter(player__user=user)
        total_answers = answers.count()
        total_correct = answers.filter(is_correct=True).count()
        accuracy = (total_correct / total_answers * 100) if total_answers > 0 else 0.0
        avg_response_time = answers.aggregate(a=Avg("response_time"))["a"] or 0.0

        # Win rate
        win_rate = (total_wins / total_games * 100) if total_games > 0 else 0.0

        # Achievements
        achievements_total = Achievement.objects.count()
        achievements_unlocked = UserAchievement.objects.filter(user=user).count()

        data = {
            "total_games_played": total_games,
            "total_wins": total_wins,
            "total_points": total_points,
            "win_rate": round(win_rate, 1),
            "avg_score_per_game": round(avg_score, 1),
            "best_score": best_score,
            "total_correct_answers": total_correct,
            "total_answers": total_answers,
            "accuracy": round(accuracy, 1),
            "avg_response_time": round(avg_response_time, 2),
            "achievements_unlocked": achievements_unlocked,
            "achievements_total": achievements_total,
        }

        serializer = UserDetailedStatsSerializer(data)
        return Response(serializer.data)


class LeaderboardView(APIView):
    """General leaderboard - top players by total points."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [LeaderboardThrottle]

    def get(self, request):
        page, page_size, offset = parse_pagination_params(request)
        leaderboard, total_count = get_global_leaderboard(offset, page_size)
        return Response(paginated_response(leaderboard, total_count, page, page_size))


class LeaderboardByModeView(APIView):
    """Leaderboard by game mode."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request, mode):
        page, page_size, offset = parse_pagination_params(request)

        # Validate mode
        valid_modes = [choice[0] for choice in GameMode.choices]
        if mode not in valid_modes:
            logger.warning(
                "leaderboard_invalid_mode",
                extra={"mode": mode, "valid_modes": valid_modes},
            )
            return Response({"error": "Mode invalide."}, status=400)

        # Aggregate scores by user for this mode
        non_superuser_ids = User.objects.filter(is_superuser=False).values_list(
            "id", flat=True
        )
        user_stats_qs = (
            GamePlayer.objects.filter(
                game__mode=mode, game__status="finished", user_id__in=non_superuser_ids
            )
            .values("user")
            .annotate(
                total_points=Sum("score"),
                total_games=Count("id"),
                total_wins=Count("id", filter=Q(rank=1)),
            )
            .order_by("-total_points")
        )

        total_count = user_stats_qs.count()
        user_stats = list(user_stats_qs[offset : offset + page_size])

        # Get user details with team memberships
        user_ids = [stat["user"] for stat in user_stats]
        users = {
            u.id: u
            for u in User.objects.filter(id__in=user_ids).prefetch_related(
                "team_memberships__team"
            )
        }

        leaderboard = []
        for idx, stat in enumerate(user_stats, offset + 1):
            user = users.get(stat["user"])
            if not user:
                continue
            win_rate = (
                (stat["total_wins"] / stat["total_games"] * 100)
                if stat["total_games"] > 0
                else 0
            )
            leaderboard.append(
                _build_leaderboard_entry(
                    idx,
                    user,
                    extra={
                        "total_points": stat["total_points"],
                        "total_games": stat["total_games"],
                        "total_wins": stat["total_wins"],
                        "win_rate": round(win_rate, 1),
                    },
                )
            )

        return Response(paginated_response(leaderboard, total_count, page, page_size))


class TeamLeaderboardView(APIView):
    """Team leaderboard - top teams by total points."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        page, page_size, offset = parse_pagination_params(request)

        # Aggregate member stats per team (sum of members' stats)
        teams_qs = Team.objects.annotate(
            sum_points=Coalesce(Sum("members__total_points"), 0),
            sum_games=Coalesce(Sum("members__total_games_played"), 0),
            sum_wins=Coalesce(Sum("members__total_wins"), 0),
        ).order_by("-sum_points", "-sum_games")

        total_count = teams_qs.count()
        teams = teams_qs[offset : offset + page_size]

        leaderboard = []
        for idx, team in enumerate(teams, offset + 1):
            total_points = int(team.sum_points or 0)
            total_games = int(team.sum_games or 0)
            total_wins = int(team.sum_wins or 0)
            win_rate = round(
                (total_wins / total_games * 100) if total_games > 0 else 0, 1
            )

            leaderboard.append(
                {
                    "rank": idx,
                    "team_id": team.id,
                    "name": team.name,
                    "avatar": team.avatar.url if team.avatar else None,
                    "owner_name": team.owner.username if team.owner else None,
                    "member_count": team.memberships.count(),
                    "total_points": total_points,
                    "total_games": total_games,
                    "total_wins": total_wins,
                    "win_rate": win_rate,
                }
            )

        return Response(paginated_response(leaderboard, total_count, page, page_size))


class MyRankView(APIView):
    """Get current user's rank in the leaderboards."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # General rank (exclude superusers)
        general_rank = (
            User.objects.filter(
                total_points__gt=user.total_points, is_superuser=False
            ).count()
            + 1
        )

        total_players = User.objects.filter(
            total_games_played__gt=0, is_superuser=False
        ).count()

        # Rank by mode
        mode_ranks = {}
        for mode_value, mode_label in GameMode.choices:
            user_points = (
                GamePlayer.objects.filter(
                    user=user, game__mode=mode_value, game__status="finished"
                ).aggregate(total=Sum("score"))["total"]
                or 0
            )

            if user_points > 0:
                higher_ranked = (
                    GamePlayer.objects.filter(
                        game__mode=mode_value, game__status="finished"
                    )
                    .values("user")
                    .annotate(total=Sum("score"))
                    .filter(total__gt=user_points)
                    .count()
                )

                mode_ranks[mode_value] = {
                    "rank": higher_ranked + 1,
                    "points": user_points,
                    "label": mode_label,
                }

        return Response(
            {
                "general_rank": general_rank,
                "total_players": total_players,
                "mode_ranks": mode_ranks,
            }
        )


class UserPublicStatsView(APIView):
    """Get public statistics for a specific user (profile page)."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = User.objects.prefetch_related("team_memberships__team").get(
                id=user_id
            )
        except (User.DoesNotExist, ValueError):
            logger.info(
                "public_stats_user_not_found",
                extra={"user_id": user_id},
            )
            return Response({"error": "Utilisateur introuvable."}, status=404)

        # Do not expose public profiles for superusers
        if getattr(user, "is_superuser", False):
            return Response({"error": "Utilisateur introuvable."}, status=404)

        # Game stats from GamePlayer records
        game_players = GamePlayer.objects.filter(user=user, rank__isnull=False)
        total_games = game_players.count()
        total_wins = game_players.filter(rank=1).count()
        total_points = game_players.aggregate(s=Sum("score"))["s"] or 0
        best_score = game_players.aggregate(m=Max("score"))["m"] or 0
        avg_score = game_players.aggregate(a=Avg("score"))["a"] or 0.0

        # Answer stats
        answers = GameAnswer.objects.filter(player__user=user)
        total_answers = answers.count()
        total_correct = answers.filter(is_correct=True).count()
        accuracy = (total_correct / total_answers * 100) if total_answers > 0 else 0.0
        avg_response_time = answers.aggregate(a=Avg("response_time"))["a"] or 0.0

        # Win rate
        win_rate = (total_wins / total_games * 100) if total_games > 0 else 0.0

        # Achievements
        achievements_total = Achievement.objects.count()
        achievements_unlocked = UserAchievement.objects.filter(user=user).count()

        # Team info
        team_membership = user.team_memberships.first()
        team_info = None
        if team_membership:
            team_info = {
                "id": str(team_membership.team.id),
                "name": team_membership.team.name,
            }

        return Response(
            {
                "user_id": str(user.id),
                "username": user.username,
                "avatar": user.avatar.url if user.avatar else None,
                "date_joined": user.created_at.isoformat(),
                "team": team_info,
                "stats": {
                    "total_games_played": total_games,
                    "total_wins": total_wins,
                    "total_points": total_points,
                    "win_rate": round(win_rate, 1),
                    "avg_score_per_game": round(avg_score, 1),
                    "best_score": best_score,
                    "total_correct_answers": total_correct,
                    "total_answers": total_answers,
                    "accuracy": round(accuracy, 1),
                    "avg_response_time": round(avg_response_time, 2),
                    "achievements_unlocked": achievements_unlocked,
                    "achievements_total": achievements_total,
                },
            }
        )
