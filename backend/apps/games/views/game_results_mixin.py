"""Results mixin: results JSON and PDF download."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..game_results_service import build_rankings, build_rounds_detail
from ..models import GamePlayer
from ..serializers import GamePlayerSerializer, GameSerializer


class GameResultsMixin:
    """Actions liées à l'affichage et l'export des résultats de partie."""

    if TYPE_CHECKING:
        def get_object(self) -> Any: ...

    @action(detail=True, methods=["get"])
    def results(self, request, room_code=None):
        """Get final results and rankings with per-round breakdown."""
        game = self.get_object()

        if not GamePlayer.objects.filter(game=game, user=request.user).exists():
            return Response(
                {"error": "Vous n'êtes pas dans cette partie."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Précharger rounds + answers via le service partagé
        rounds_detail, _ = build_rounds_detail(game)

        players = game.competitive_players().select_related("user").order_by("-score")

        game_data = GameSerializer(game).data
        # Add user-friendly display fields (used by frontend)
        game_data["mode_display"] = game.get_mode_display()
        game_data["answer_mode_display"] = game.get_answer_mode_display()
        game_data["guess_target_display"] = game.get_guess_target_display()

        return Response(
            {
                "game": game_data,
                "rankings": GamePlayerSerializer(players, many=True).data,
                "rounds": rounds_detail,
            }
        )

    @action(detail=True, methods=["get"], url_path="results/pdf")
    def results_pdf(self, request, room_code=None):
        """Download game results as PDF."""
        from django.http import HttpResponse

        from ..pdf_service import generate_results_pdf

        game = self.get_object()

        if not GamePlayer.objects.filter(game=game, user=request.user).exists():
            return Response(
                {"error": "Vous n'êtes pas dans cette partie."},
                status=status.HTTP_403_FORBIDDEN,
            )

        rankings = build_rankings(game)
        rounds_detail, _ = build_rounds_detail(game)

        game_data = {
            "room_code": game.room_code,
            "mode_display": game.get_mode_display(),
            "answer_mode_display": game.get_answer_mode_display(),
            "guess_target_display": game.get_guess_target_display(),
            "num_rounds": game.num_rounds,
            "name": game.name,
            "started_at": (game.started_at.isoformat() if game.started_at else None),
            "finished_at": (game.finished_at.isoformat() if game.finished_at else None),
        }

        pdf_bytes = generate_results_pdf(game_data, rankings, rounds_detail)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="instantmusic_resultats_{room_code}.pdf"'
        )
        return response
