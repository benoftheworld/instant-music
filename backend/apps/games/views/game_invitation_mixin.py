"""Invitation mixin: invite, list, accept, decline."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import GamePlayer
from ..models.game_invitation import GameInvitation, InvitationStatus
from ..permissions import IsGameHost
from ..serializers import GameInvitationSerializer

logger = logging.getLogger(__name__)


class GameInvitationMixin:
    """Actions liées aux invitations de partie."""

    if TYPE_CHECKING:
        def get_object(self) -> Any: ...
        def _broadcast_player_join(self, game: Any, player: Any, room_code: Any, request: Any) -> None: ...

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated, IsGameHost])
    def invite(self, request, room_code=None):
        """Invite a friend to the current lobby (host only)."""
        game = self.get_object()

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
            self._broadcast_player_join(game, _player, game.room_code, request)

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
