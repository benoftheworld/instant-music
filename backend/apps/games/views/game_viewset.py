"""ViewSet for Game model."""

from __future__ import annotations

import logging
import random
import string

from django.db.models import Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Game, GameAnswer, GamePlayer
from ..serializers import (
    CreateGameSerializer,
    GameAnswerSerializer,
    GameHistorySerializer,
    GamePlayerSerializer,
    GameRoundSerializer,
    GameSerializer,
    LeaderboardSerializer,
)
from ..services import game_service
from ..broadcast_service import (
    broadcast_game_finish,
    broadcast_next_round,
    broadcast_player_join,
    broadcast_round_end,
    broadcast_round_start,
)

logger = logging.getLogger(__name__)


def generate_room_code() -> str:
    """Generate a unique 6-character room code."""
    while True:
        code = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)
        )
        if not Game.objects.filter(room_code=code).exists():
            return code


class GameViewSet(viewsets.ModelViewSet):
    """ViewSet for Game model."""

    queryset = Game.objects.all()
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "room_code"

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == "create":
            return CreateGameSerializer
        return GameSerializer

    def create(self, request):
        """Create a new game."""
        serializer = CreateGameSerializer(data=request.data)

        if serializer.is_valid():
            game = serializer.save(
                host=request.user, room_code=generate_room_code()
            )
            GamePlayer.objects.create(game=game, user=request.user)
            return Response(
                GameSerializer(game).data, status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def join(self, request, room_code=None):
        """Join a game."""
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

        game.refresh_from_db()
        game_serializer = GameSerializer(game, context={"request": request})
        player_serializer = GamePlayerSerializer(
            player, context={"request": request}
        )

        broadcast_player_join(
            room_code,
            player_data=player_serializer.data,
            game_data=game_serializer.data,
        )

        return Response(player_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def start(self, request, room_code=None):
        """Start a game and generate rounds."""
        game = self.get_object()

        if game.host != request.user:
            return Response(
                {"error": "Seul l'hôte peut démarrer la partie."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if game.status == "in_progress":
            existing_rounds = game.rounds.all().order_by("round_number")
            first_round = existing_rounds.first()
            return Response(
                {
                    "game": GameSerializer(game).data,
                    "rounds_created": existing_rounds.count(),
                    "first_round": (
                        GameRoundSerializer(first_round).data
                        if first_round
                        else None
                    ),
                },
                status=status.HTTP_200_OK,
            )

        min_players = 1 if game.mode == "karaoke" else 2
        if game.players.count() < min_players:
            msg = (
                "Au moins 1 joueur est nécessaire."
                if game.mode == "karaoke"
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

            if rounds:
                broadcast_round_start(room_code, rounds[0])

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
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(
                "Unexpected error starting game %s: %s", room_code, e
            )
            return Response(
                {"error": f"Erreur inattendue: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["get"], url_path="current-round")
    def current_round(self, request, room_code=None):
        """Get the current round of the game."""
        game = self.get_object()

        if not GamePlayer.objects.filter(
            game=game, user=request.user
        ).exists():
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
            return Response(
                {"current_round": None, "message": "Partie terminée"}
            )

        return Response(
            {"current_round": GameRoundSerializer(round_obj).data}
        )

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
        response_time = request.data.get("response_time", 0)

        if not answer_text:
            return Response(
                {"error": "Aucune réponse fournie."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            game_answer = game_service.submit_answer(
                player=player,
                round_obj=round_obj,
                answer=answer_text,
                response_time=float(response_time),
            )

            total_players = game.players.count()
            answered_players = GameAnswer.objects.filter(
                round=round_obj
            ).count()

            if answered_players >= total_players:
                round_obj.ended_at = timezone.now()
                round_obj.save()
                broadcast_round_end(room_code, round_obj, game)

            return Response(
                GameAnswerSerializer(game_answer).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=["post"], url_path="end-round")
    def end_current_round(self, request, room_code=None):
        """End the current round and broadcast results (host only)."""
        game = self.get_object()

        if game.host != request.user:
            return Response(
                {"error": "Seul l'hôte peut terminer le round."},
                status=status.HTTP_403_FORBIDDEN,
            )

        current = game_service.get_current_round(game)
        if not current:
            return Response(
                {"error": "Aucun round actif."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if current.ended_at:
            return Response(
                {"message": "Round déjà terminé."},
                status=status.HTTP_200_OK,
            )

        game_service.end_round(current)

        try:
            current.refresh_from_db()
            broadcast_round_end(room_code, current, game)
            return Response(
                {
                    "message": "Round terminé.",
                    "correct_answer": current.correct_answer,
                },
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.exception("Failed to end round")
            return Response(
                {"error": "Erreur lors de la fin du round."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], url_path="next-round")
    def next_round(self, request, room_code=None):
        """Move to the next round (host only)."""
        game = self.get_object()

        if game.host != request.user:
            return Response(
                {"error": "Seul l'hôte peut passer au round suivant."},
                status=status.HTTP_403_FORBIDDEN,
            )

        current = game_service.get_current_round(game)
        if current:
            game_service.end_round(current)
            try:
                current.refresh_from_db()
                broadcast_round_end(room_code, current, game)
            except Exception:
                logger.exception(
                    "Failed to broadcast round_end on timeout"
                )

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

    @action(detail=True, methods=["get"])
    def results(self, request, room_code=None):
        """Get final results and rankings with per-round breakdown."""
        game = self.get_object()

        if not GamePlayer.objects.filter(
            game=game, user=request.user
        ).exists():
            return Response(
                {"error": "Vous n'êtes pas dans cette partie."},
                status=status.HTTP_403_FORBIDDEN,
            )

        players = game.players.order_by("-score")

        rounds_detail = []
        for r in game.rounds.order_by("round_number"):
            answers = [
                {
                    "username": ans.player.user.username,
                    "answer": ans.answer,
                    "is_correct": ans.is_correct,
                    "points_earned": ans.points_earned,
                    "response_time": round(ans.response_time, 1),
                }
                for ans in r.answers.select_related("player__user").order_by(
                    "-points_earned"
                )
            ]
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

        return Response(
            {
                "game": GameSerializer(game).data,
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

        if not GamePlayer.objects.filter(
            game=game, user=request.user
        ).exists():
            return Response(
                {"error": "Vous n'êtes pas dans cette partie."},
                status=status.HTTP_403_FORBIDDEN,
            )

        players = game.players.order_by("-score")
        rankings = [
            {
                "username": p.user.username,
                "score": p.score,
                "rank": p.rank,
            }
            for p in players
        ]

        rounds_detail = []
        for r in game.rounds.order_by("round_number"):
            answers = [
                {
                    "username": ans.player.user.username,
                    "answer": ans.answer,
                    "is_correct": ans.is_correct,
                    "points_earned": ans.points_earned,
                    "response_time": round(ans.response_time, 1),
                }
                for ans in r.answers.select_related("player__user").order_by(
                    "-points_earned"
                )
            ]
            rounds_detail.append(
                {
                    "round_number": r.round_number,
                    "track_name": r.track_name,
                    "artist_name": r.artist_name,
                    "correct_answer": r.correct_answer,
                    "answers": answers,
                }
            )

        game_data = {
            "room_code": game.room_code,
            "mode": game.get_mode_display(),
            "name": game.name,
        }

        pdf_bytes = generate_results_pdf(game_data, rankings, rounds_detail)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        response["Content-Disposition"] = (
            f'attachment; filename="instantmusic_resultats_{room_code}.pdf"'
        )
        return response

    @action(detail=False, methods=["get"])
    def available(self, request):
        """Get list of available games to join."""
        games = Game.objects.filter(status="waiting", is_online=True)
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[])
    def history(self, request):
        """Get game history (finished games)."""
        limit = request.query_params.get("limit", None)

        games = (
            Game.objects.filter(status="finished")
            .select_related("host")
            .prefetch_related("players__user")
            .order_by("-finished_at")
        )

        if limit:
            try:
                games = games[: int(limit)]
            except ValueError:
                pass

        serializer = GameHistorySerializer(
            games, many=True, context={"request": request}
        )
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[])
    def leaderboard(self, request):
        """Get global leaderboard of top players."""
        from apps.users.models import User

        limit = request.query_params.get("limit", 10)
        try:
            limit = int(limit)
        except ValueError:
            limit = 10

        leaderboard_data = []
        users = User.objects.filter(
            game_participations__isnull=False
        ).distinct()

        for user in users:
            participations = GamePlayer.objects.filter(
                user=user, game__status="finished"
            )

            total_games = participations.count()
            if total_games == 0:
                continue

            total_points = (
                participations.aggregate(total=Sum("score"))["total"] or 0
            )
            total_wins = participations.filter(rank=1).count()
            win_rate = (
                (total_wins / total_games * 100) if total_games > 0 else 0
            )

            leaderboard_data.append(
                {
                    "user_id": user.id,
                    "username": user.username,
                    "avatar": user.avatar.url if user.avatar else None,
                    "total_games": total_games,
                    "total_wins": total_wins,
                    "total_points": total_points,
                    "win_rate": round(win_rate, 1),
                }
            )

        leaderboard_data.sort(key=lambda x: x["total_points"], reverse=True)
        leaderboard_data = leaderboard_data[:limit]

        serializer = LeaderboardSerializer(leaderboard_data, many=True)
        return Response(serializer.data)
