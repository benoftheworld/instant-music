"""Round gameplay mixin: current-round, answer, end-round, next-round."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..broadcast_service import (
    broadcast_game_finish,
    broadcast_next_round,
    broadcast_round_end,
)
from ..models import GameAnswer, GamePlayer, GameRound
from ..permissions import IsGameHost
from ..serializers import (
    GameAnswerSerializer,
    GameRoundSerializer,
    GameSerializer,
)
from ..services import game_service

logger = logging.getLogger(__name__)


class GameRoundMixin:
    """Actions liées au déroulement des manches (réponses, transitions)."""

    if TYPE_CHECKING:

        def get_object(self) -> Any: ...  # noqa: D102

    @action(detail=True, methods=["get"], url_path="current-round")
    def current_round(self, request, room_code=None):
        """Get the current round of the game."""
        game = self.get_object()

        if not GamePlayer.objects.filter(game=game, user=request.user).exists():
            return Response(
                {"error": "Vous n'êtes pas dans cette partie."},
                status=status.HTTP_403_FORBIDDEN,
            )

        round_obj = game_service.get_current_round(game)

        if not round_obj:
            next_round = game_service.get_next_round(game)
            if next_round:
                return Response(
                    {
                        "current_round": None,
                        "next_round": GameRoundSerializer(next_round).data,
                    }
                )
            return Response({"current_round": None, "message": "Partie terminée"})

        return Response({"current_round": GameRoundSerializer(round_obj).data})

    @action(detail=True, methods=["post"])
    def answer(self, request, room_code=None):
        """Submit an answer for the current round."""
        game = self.get_object()

        try:
            player = GamePlayer.objects.get(game=game, user=request.user)
        except GamePlayer.DoesNotExist:
            return Response(
                {"error": "Vous n'êtes pas dans cette partie."},
                status=status.HTTP_403_FORBIDDEN,
            )

        round_obj = game_service.get_current_round(game)
        if not round_obj:
            return Response(
                {"error": "Aucun round actif."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if GameAnswer.objects.filter(round=round_obj, player=player).exists():
            return Response(
                {"error": "Vous avez déjà répondu à ce round."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        answer_text = request.data.get("answer")

        if not answer_text:
            return Response(
                {"error": "Aucune réponse fournie."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Anti-triche : le serveur calcule le temps de réponse à partir du
        # début du round côté joueur (après l'écran de chargement),
        # pas depuis le signal backend qui inclut le timer_start_round.
        if round_obj.started_at:
            delta = (timezone.now() - round_obj.started_at).total_seconds()
            # Soustraire la durée de l'écran de chargement pré-round : le joueur
            # ne peut répondre qu'après ce délai, donc son « temps de réponse »
            # ne doit pas inclure ces secondes.
            timer_offset = float(round_obj.game.timer_start_round)
            effective_delta = max(0.0, delta - timer_offset)
            response_time = max(0.0, min(effective_delta, float(round_obj.duration)))
        else:
            response_time = 0.0

        try:
            game_answer = game_service.submit_answer(
                player=player,
                round_obj=round_obj,
                answer=answer_text,
                response_time=response_time,
            )

            # Verrou atomique pour éviter la condition de course où deux joueurs
            # répondent simultanément : sans ce verrou, les deux requêtes peuvent
            # lire le même total, mettre ended_at et broadcaster round_ended deux
            # fois → l'hôte programme deux setTimeout → appel double à next_round
            # → la partie saute des rounds et se termine prématurément.
            should_broadcast = False
            with transaction.atomic():
                locked_round = GameRound.objects.select_for_update().get(
                    id=round_obj.id
                )
                if not locked_round.ended_at:
                    total_players = game.competitive_players().count()
                    answered_players = GameAnswer.objects.filter(
                        round=locked_round
                    ).count()
                    if answered_players >= total_players:
                        locked_round.ended_at = timezone.now()
                        locked_round.save()
                        should_broadcast = True

            if should_broadcast:
                round_obj.refresh_from_db()
                broadcast_round_end(room_code, round_obj, game)

            return Response(
                GameAnswerSerializer(game_answer).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=True,
        methods=["post"],
        url_path="end-round",
        permission_classes=[IsAuthenticated, IsGameHost],
    )
    def end_current_round(self, request, room_code=None):
        """End the current round and broadcast results (host only)."""
        game = self.get_object()

        current = game_service.get_current_round(game)
        if not current:
            return Response(
                {"error": "Aucune manche active."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if current.ended_at:
            return Response(
                {"message": "Manche déjà terminée."},
                status=status.HTTP_200_OK,
            )

        game_service.end_round(current)

        try:
            current.refresh_from_db()
            broadcast_round_end(room_code, current, game)
            return Response(
                {
                    "message": "Manche terminée.",
                    "correct_answer": current.correct_answer,
                },
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.exception("Failed to end round")
            return Response(
                {"error": "Erreur lors de la fin de la manche."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=["post"],
        url_path="next-round",
        permission_classes=[IsAuthenticated, IsGameHost],
    )
    def next_round(self, request, room_code=None):
        """Move to the next round (host only)."""
        game = self.get_object()

        current = game_service.get_current_round(game)
        if current:
            game_service.end_round(current)
            try:
                current.refresh_from_db()
                broadcast_round_end(room_code, current, game)
            except Exception:
                logger.exception("Failed to broadcast round_end on timeout")

        next_rnd = game_service.get_next_round(game)

        if not next_rnd:
            game = game_service.finish_game(game)
            broadcast_game_finish(room_code, game)
            return Response(
                {
                    "game": GameSerializer(game).data,
                    "message": "Partie terminée",
                }
            )

        game_service.start_round(next_rnd)
        next_rnd.refresh_from_db()
        broadcast_next_round(room_code, next_rnd, game)
        return Response(GameRoundSerializer(next_rnd).data)
