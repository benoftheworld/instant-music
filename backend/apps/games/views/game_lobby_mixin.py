"""Lobby management mixin: create, join, leave, start."""

from __future__ import annotations

import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..broadcast_service import (
    broadcast_game_start,
    broadcast_game_update,
    broadcast_player_join,
    broadcast_player_leave,
    broadcast_round_start,
)
from ..models import GamePlayer
from ..permissions import IsGameHost
from ..serializers import (
    CreateGameSerializer,
    GamePlayerSerializer,
    GameRoundSerializer,
    GameSerializer,
)
from ..services import game_service
from .utils import _maintenance_response_if_needed, generate_room_code

logger = logging.getLogger(__name__)


class GameLobbyMixin:
    """Actions liées à la gestion du lobby (création, rejoindre, quitter, démarrer)."""

    def _broadcast_player_join(self, game, player, room_code, request):
        """Refresh game, serialize, and broadcast a player_join event."""
        game.refresh_from_db()
        game_serializer = GameSerializer(game, context={"request": request})
        player_serializer = GamePlayerSerializer(player, context={"request": request})
        broadcast_player_join(
            room_code,
            player_data=player_serializer.data,
            game_data=game_serializer.data,
        )

    def create(self, request):
        """Create a new game."""
        if maint := _maintenance_response_if_needed(request.user):
            return maint

        serializer = CreateGameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        game = serializer.save(host=request.user, room_code=generate_room_code())
        GamePlayer.objects.create(game=game, user=request.user)
        return Response(GameSerializer(game).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, room_code=None):
        """PATCH a game and broadcast the update to all lobby clients."""
        game = self.get_object()
        serializer = GameSerializer(game, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        game.refresh_from_db()
        game_data = GameSerializer(game, context={"request": request}).data
        try:
            broadcast_game_update(room_code, game_data)
        except Exception:
            logger.warning("Failed to broadcast game update for %s", room_code)
        return Response(game_data)

    @action(detail=True, methods=["post"])
    def join(self, request, room_code=None):
        """Join a game."""
        if maint := _maintenance_response_if_needed(request.user):
            return maint

        game = self.get_object()

        if game.status != "waiting":
            return Response(
                {"error": "La partie a déjà commencé."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if game.players.count() >= game.max_players:
            return Response(
                {"error": "La partie est pleine."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if GamePlayer.objects.filter(game=game, user=request.user).exists():
            return Response(
                {"error": "Vous êtes déjà dans cette partie."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        player = GamePlayer.objects.create(game=game, user=request.user)

        self._broadcast_player_join(game, player, room_code, request)

        player_serializer = GamePlayerSerializer(player, context={"request": request})
        return Response(player_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def leave(self, request, room_code=None):
        """Leave a game (remove player from the game)."""
        game = self.get_object()

        if game.status not in ("waiting",):
            return Response(
                {"error": "Impossible de quitter une partie en cours."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            player = GamePlayer.objects.get(game=game, user=request.user)
        except GamePlayer.DoesNotExist:
            return Response(
                {"error": "Vous n'êtes pas dans cette partie."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Host cannot leave — they should cancel the game instead
        if game.host == request.user:
            # Cancel the game when the host leaves
            game.status = "cancelled"
            game.save(update_fields=["status"])
            player.delete()
            game.refresh_from_db()
            game_serializer = GameSerializer(game, context={"request": request})
            broadcast_player_leave(
                room_code,
                player_data={
                    "user": request.user.id,
                    "username": request.user.username,
                },
                game_data=game_serializer.data,
            )
            return Response({"message": "Partie annulée (l'hôte a quitté)."})

        player.delete()
        game.refresh_from_db()
        game_serializer = GameSerializer(game, context={"request": request})
        broadcast_player_leave(
            room_code,
            player_data={
                "user": request.user.id,
                "username": request.user.username,
            },
            game_data=game_serializer.data,
        )

        return Response({"message": "Vous avez quitté la partie."})

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsGameHost])
    def start(self, request, room_code=None):
        """Start a game and generate rounds."""
        game = self.get_object()

        if game.status == "in_progress":
            existing_rounds = game.rounds.all().order_by("round_number")
            first_round = existing_rounds.first()
            return Response(
                {
                    "game": GameSerializer(game).data,
                    "rounds_created": existing_rounds.count(),
                    "first_round": (
                        GameRoundSerializer(first_round).data if first_round else None
                    ),
                },
                status=status.HTTP_200_OK,
            )

        min_players = 1 if game.mode == "karaoke" or not game.is_online else 2
        if game.is_party_mode:
            # En mode soirée, le présentateur (hôte) ne compte pas comme joueur
            non_host_players = game.competitive_players().count()
            if non_host_players < 1:
                return Response(
                    {"error": "Il faut au moins 1 joueur (hors présentateur) pour démarrer en mode soirée."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        elif game.players.count() < min_players:
            msg = (
                "Au moins 1 joueur est nécessaire."
                if game.mode == "karaoke" or not game.is_online
                else "Au moins 2 joueurs sont nécessaires."
            )
            return Response(
                {"error": msg},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if game.mode != "karaoke" and not game.playlist_id:
            return Response(
                {"error": "Veuillez sélectionner une playlist."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            game, rounds = game_service.start_game(game)

            # Broadcast game_started FIRST so all clients navigate to play page,
            # then broadcast round_started so they receive the first round data.
            broadcast_game_start(room_code, game)

            if rounds:
                broadcast_round_start(room_code, rounds[0], game)

            return Response(
                {
                    "game": GameSerializer(game).data,
                    "rounds_created": len(rounds),
                    "first_round": (
                        GameRoundSerializer(rounds[0]).data if rounds else None
                    ),
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            logger.error("Failed to start game %s: %s", room_code, e)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Unexpected error starting game %s", room_code)
            return Response(
                {"error": "Une erreur inattendue est survenue. Veuillez réessayer."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
