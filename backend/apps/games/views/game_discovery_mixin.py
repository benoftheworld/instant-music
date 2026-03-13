"""Discovery mixin: public games listing, history, leaderboard."""

from __future__ import annotations

from django.db.models import Count, Q
from rest_framework import permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core.pagination import paginated_response, parse_pagination_params

from ..models import Game
from ..models.enums import GameMode
from ..serializers import GameHistorySerializer, GameSerializer


class GameDiscoveryMixin:
    """Actions de découverte : parties publiques, historique, classement global."""

    @action(detail=False, methods=["get"], url_path="public")
    def public_games(self, request):
        """Get list of public games waiting for players."""
        page, page_size, offset = parse_pagination_params(request)
        games = (
            Game.objects.filter(status="waiting", is_public=True, is_online=True)
            .select_related("host")
            .prefetch_related("players")
            .annotate(_player_count=Count("players"))
            .order_by("-created_at")
        )
        search = request.query_params.get("search", "").strip()
        if search:
            games = games.filter(
                Q(name__icontains=search)
                | Q(room_code__icontains=search)
                | Q(playlist_name__icontains=search)
                | Q(host__username__icontains=search)
            )
        total_count = games.count()
        page_games = games[offset : offset + page_size]
        serializer = GameSerializer(page_games, many=True)
        return Response(paginated_response(serializer.data, total_count, page, page_size))

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.AllowAny],
        authentication_classes=[],
    )
    def history(self, request):
        """Get game history (finished games)."""
        page, page_size, offset = parse_pagination_params(request)

        games_qs = (
            Game.objects.filter(status="finished")
            .select_related("host")
            .prefetch_related("players__user")
            .order_by("-finished_at")
        )

        # Optional mode filter
        mode = request.query_params.get("mode", None)
        if mode:
            valid_modes = [choice[0] for choice in GameMode.choices]
            if mode in valid_modes:
                games_qs = games_qs.filter(mode=mode)

        total_count = games_qs.count()
        games = games_qs[offset : offset + page_size]

        serializer = GameHistorySerializer(
            games, many=True, context={"request": request}
        )
        return Response(
            paginated_response(serializer.data, total_count, page, page_size)
        )

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.AllowAny],
        authentication_classes=[],
    )
    def leaderboard(self, request):
        """Get global leaderboard of top players.

        Delegates to :func:`apps.stats.services.get_global_leaderboard` for
        shared logic without the view-calling-view anti-pattern.
        """
        from apps.stats.services import get_global_leaderboard

        page, page_size, offset = parse_pagination_params(request)
        data, total_count = get_global_leaderboard(offset, page_size)
        return Response(paginated_response(data, total_count, page, page_size))
