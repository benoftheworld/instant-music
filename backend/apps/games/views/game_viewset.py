"""ViewSet for Game model."""

from __future__ import annotations

import logging
import random
import string

from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core.pagination import paginated_response, parse_pagination_params
from apps.core.throttles import GameCreateThrottle, GameJoinThrottle

from ..broadcast_service import (
    broadcast_game_finish,
    broadcast_game_update,
    broadcast_next_round,
    broadcast_player_join,
    broadcast_player_leave,
    broadcast_round_end,
    broadcast_round_start,
)
from ..game_results_service import build_rankings, build_rounds_detail
from ..models import Game, GameAnswer, GamePlayer, GameRound
from ..models.enums import GameMode
from ..models.game_invitation import GameInvitation, InvitationStatus
from ..serializers import (
    CreateGameSerializer,
    GameAnswerSerializer,
    GameHistorySerializer,
    GameInvitationSerializer,
    GamePlayerSerializer,
    GameRoundSerializer,
    GameSerializer,
)
from ..services import game_service

logger = logging.getLogger(__name__)


def generate_room_code() -> str:
    """Generate a unique 6-character room code."""
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Game.objects.filter(room_code=code).exists():
            return code


def _maintenance_response_if_needed(user) -> Response | None:
    """Retourne une 503 si le site est en maintenance et que l'user n'est pas staff.

    Vérification de défense en profondeur : le MaintenanceMiddleware bloque déjà
    les non-staff au niveau HTTP, mais ce contrôle offre un message d'erreur
    spécifique aux opérations de jeu.
    """
    from apps.administration.models import SiteConfiguration

    try:
        cfg = SiteConfiguration.get_solo()
    except Exception:
        return None  # table absente (migrations en attente) — on laisse passer

    if not cfg.maintenance_mode:
        return None

    if user.is_staff:
        return None  # les staff peuvent toujours créer/rejoindre des parties

    return Response(
        {
            "error": "Le site est en cours de maintenance. Impossible de créer ou rejoindre une partie pour le moment.",
            "maintenance": True,
            "maintenance_title": cfg.maintenance_title,
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )


class GameViewSet(viewsets.ModelViewSet):
    """ViewSet for Game model."""

    queryset = Game.objects.select_related("host")
    serializer_class = GameSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "room_code"

    def get_throttles(self):
        if self.action == "create":
            return [GameCreateThrottle()]
        if self.action == "join":
            return [GameJoinThrottle()]
        return super().get_throttles()

    def get_serializer_class(self):
        """Return appropriate serializer class."""
        if self.action == "create":
            return CreateGameSerializer
        return GameSerializer

    def create(self, request):
        """Create a new game."""
        if maint := _maintenance_response_if_needed(request.user):
            return maint

        serializer = CreateGameSerializer(data=request.data)

        if serializer.is_valid():
            game = serializer.save(host=request.user, room_code=generate_room_code())
            GamePlayer.objects.create(game=game, user=request.user)
            return Response(GameSerializer(game).data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, room_code=None):
        """PATCH a game and broadcast the update to all lobby clients."""
        game = self.get_object()
        serializer = GameSerializer(game, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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

        game.refresh_from_db()
        game_serializer = GameSerializer(game, context={"request": request})
        player_serializer = GamePlayerSerializer(player, context={"request": request})

        broadcast_player_join(
            room_code,
            player_data=player_serializer.data,
            game_data=game_serializer.data,
        )

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
                        GameRoundSerializer(first_round).data if first_round else None
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
                    total_players = game.players.count()
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

        players = game.players.select_related("user").order_by("-score")

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

    @action(detail=False, methods=["get"])
    def available(self, request):
        """Get list of available games to join (public games only)."""
        games = Game.objects.filter(status="waiting", is_online=True, is_public=True)
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="public")
    def public_games(self, request):
        """Get list of public games waiting for players."""
        games = (
            Game.objects.filter(status="waiting", is_public=True, is_online=True)
            .select_related("host")
            .prefetch_related("players")
            .annotate(_player_count=Count("players"))
            .order_by("-created_at")
        )
        search = request.query_params.get("search", "").strip()
        if search:
            from django.db.models import Q

            games = games.filter(
                Q(name__icontains=search)
                | Q(room_code__icontains=search)
                | Q(playlist_name__icontains=search)
                | Q(host__username__icontains=search)
            )
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.AllowAny],
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

    # ── Invitation actions ────────────────────────────────────────────────────

    @action(detail=True, methods=["post"])
    def invite(self, request, room_code=None):
        """Invite a friend to the current lobby (host only)."""
        game = self.get_object()

        if game.host != request.user:
            return Response(
                {"error": "Seul l'hôte peut inviter des joueurs."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if game.status != "waiting":
            return Response(
                {"error": "La partie a déjà commencé ou est terminée."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        username = request.data.get("username", "").strip()
        if not username:
            return Response(
                {"error": "Nom d'utilisateur requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from apps.users.models import User as AppUser

        try:
            recipient = AppUser.objects.get(username=username)
        except AppUser.DoesNotExist:
            return Response(
                {"error": "Utilisateur introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if recipient == request.user:
            return Response(
                {"error": "Vous ne pouvez pas vous inviter vous-même."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if GamePlayer.objects.filter(game=game, user=recipient).exists():
            return Response(
                {"error": f"{username} est déjà dans la partie."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if game.players.count() >= game.max_players:
            return Response(
                {"error": "La partie est pleine."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Cancel any existing invitation for this recipient in this game
        GameInvitation.objects.filter(
            game=game,
            recipient=recipient,
            status=InvitationStatus.PENDING,
        ).update(status=InvitationStatus.CANCELLED)

        invitation = GameInvitation.objects.create(
            game=game,
            sender=request.user,
            recipient=recipient,
        )

        # Vérifier l'achievement "L'inviteur"
        try:
            from apps.achievements.services import achievement_service

            request.user.refresh_from_db()
            achievement_service.check_and_award(request.user)
        except Exception:  # noqa: BLE001
            pass

        # Push WS notification to recipient
        invitation_data = GameInvitationSerializer(invitation).data
        try:
            from asgiref.sync import async_to_sync
            from channels.layers import get_channel_layer

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{recipient.id}",
                {
                    "type": "notify.game_invitation",
                    "invitation": invitation_data,
                },
            )
        except Exception:
            logger.exception("Failed to push WS notification for invitation")

        return Response(invitation_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="my-invitations")
    def my_invitations(self, request):
        """List pending game invitations received by the current user."""
        from django.utils import timezone as tz

        invitations = (
            GameInvitation.objects.filter(
                recipient=request.user,
                status=InvitationStatus.PENDING,
            )
            .select_related("game", "sender", "recipient")
            .filter(expires_at__gt=tz.now())
        )
        return Response(GameInvitationSerializer(invitations, many=True).data)

    @action(
        detail=False,
        methods=["post"],
        url_path="invitations/(?P<invitation_id>[^/.]+)/accept",
    )
    def accept_invitation(self, request, invitation_id=None, room_code=None):
        """Accept a game invitation and auto-join the lobby."""
        try:
            invitation = GameInvitation.objects.select_related(
                "game", "sender", "recipient"
            ).get(id=invitation_id, recipient=request.user)
        except GameInvitation.DoesNotExist:
            return Response(
                {"error": "Invitation introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if invitation.status != InvitationStatus.PENDING:
            return Response(
                {"error": "Cette invitation n'est plus valide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if invitation.is_expired:
            invitation.status = InvitationStatus.EXPIRED
            invitation.save(update_fields=["status"])
            return Response(
                {"error": "L'invitation a expiré."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        game = invitation.game

        if game.status != "waiting":
            invitation.status = InvitationStatus.EXPIRED
            invitation.save(update_fields=["status"])
            return Response(
                {"error": "La partie n'est plus disponible."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if game.players.count() >= game.max_players:
            return Response(
                {"error": "La partie est pleine."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation.status = InvitationStatus.ACCEPTED
        invitation.save(update_fields=["status"])

        # Join the game if not already in it
        _player, created = GamePlayer.objects.get_or_create(
            game=game, user=request.user
        )

        if created:
            game.refresh_from_db()
            game_serializer = GameSerializer(game, context={"request": request})
            player_serializer = GamePlayerSerializer(
                _player, context={"request": request}
            )
            broadcast_player_join(
                game.room_code,
                player_data=player_serializer.data,
                game_data=game_serializer.data,
            )

        return Response(
            {
                "room_code": game.room_code,
                "message": "Invitation acceptée. Vous rejoignez la partie.",
            }
        )

    @action(
        detail=False,
        methods=["post"],
        url_path="invitations/(?P<invitation_id>[^/.]+)/decline",
    )
    def decline_invitation(self, request, invitation_id=None, room_code=None):
        """Decline a game invitation."""
        try:
            invitation = GameInvitation.objects.get(
                id=invitation_id, recipient=request.user
            )
        except GameInvitation.DoesNotExist:
            return Response(
                {"error": "Invitation introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if invitation.status != InvitationStatus.PENDING:
            return Response(
                {"error": "Cette invitation n'est plus valide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invitation.status = InvitationStatus.DECLINED
        invitation.save(update_fields=["status"])
        return Response({"message": "Invitation refusée."})
