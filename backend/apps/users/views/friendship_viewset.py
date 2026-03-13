"""ViewSet for managing friendships."""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import Friendship, FriendshipStatus, User
from ..serializers import (
    FriendshipCreateSerializer,
    FriendshipSerializer,
    UserMinimalSerializer,
)

logger = logging.getLogger("apps.users.views")


class FriendshipViewSet(viewsets.ViewSet):
    """ViewSet for managing friendships."""

    permission_classes = [IsAuthenticated]

    def list(self, request):
        """List all friends (accepted friendships). Exclude superuser friends."""
        user = request.user
        friendships = Friendship.objects.filter(
            Q(from_user=user, status=FriendshipStatus.ACCEPTED)
            | Q(to_user=user, status=FriendshipStatus.ACCEPTED)
        ).select_related("from_user", "to_user")

        friends = []
        for f in friendships:
            friend = f.to_user if f.from_user == user else f.from_user
            # Exclude superuser friends from the list
            if friend.is_superuser:
                continue
            friends.append(
                {
                    "friendship_id": f.id,
                    "user": UserMinimalSerializer(friend).data,
                    "since": f.updated_at,
                }
            )

        return Response(friends)

    @action(detail=False, methods=["get"])
    def pending(self, request):
        """List pending friend requests received."""
        requests_qs = Friendship.objects.filter(
            to_user=request.user,
            status=FriendshipStatus.PENDING,
        ).select_related("from_user", "to_user")

        return Response(FriendshipSerializer(requests_qs, many=True).data)

    @action(detail=False, methods=["get"])
    def sent(self, request):
        """List friend requests sent."""
        requests_qs = Friendship.objects.filter(
            from_user=request.user,
            status=FriendshipStatus.PENDING,
        ).select_related("from_user", "to_user")

        return Response(FriendshipSerializer(requests_qs, many=True).data)

    @action(detail=False, methods=["post"])
    def send_request(self, request):
        """Send a friend request. Cannot send to superusers."""
        serializer = FriendshipCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        to_user = User.objects.get(username=username)

        if to_user == request.user:
            return Response(
                {"error": "Vous ne pouvez pas vous ajouter vous-même."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if to_user.is_superuser:
            return Response(
                {"error": "Impossible d'ajouter cet utilisateur."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        existing = Friendship.objects.filter(
            Q(from_user=request.user, to_user=to_user)
            | Q(from_user=to_user, to_user=request.user)
        ).first()

        if existing:
            if existing.status == FriendshipStatus.ACCEPTED:
                return Response(
                    {"error": "Vous êtes déjà amis."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif existing.status == FriendshipStatus.PENDING:
                return Response(
                    {"error": "Une demande est déjà en cours."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        friendship = Friendship.objects.create(
            from_user=request.user,
            to_user=to_user,
            status=FriendshipStatus.PENDING,
        )

        # Notifier le destinataire en temps réel
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{to_user.id}",
                {
                    "type": "notify.friend_request",
                    "friendship": FriendshipSerializer(friendship).data,
                },
            )
        except Exception:  # noqa: BLE001
            logger.exception("Échec de la notification WS pour la demande d'ami")

        return Response(
            FriendshipSerializer(friendship).data,
            status=status.HTTP_201_CREATED,
        )
    def accept(self, request, pk=None):
        """Accept a friend request."""
        try:
            friendship = Friendship.objects.get(
                id=pk,
                to_user=request.user,
                status=FriendshipStatus.PENDING,
            )
        except Friendship.DoesNotExist:
            return Response(
                {"error": "Demande introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        friendship.status = FriendshipStatus.ACCEPTED
        friendship.save()

        # Vérifier l'achievement "Sociable" pour les deux utilisateurs
        try:
            from apps.achievements.services import achievement_service

            for u in (friendship.from_user, friendship.to_user):
                u.refresh_from_db()
                achievement_service.check_and_award(u)
        except Exception:  # noqa: BLE001
            logger.exception("Échec du check achievement Sociable")

        # Notifier l'expéditeur que sa demande a été acceptée
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{friendship.from_user.id}",
                {
                    "type": "notify.friend_request_accepted",
                    "friendship": FriendshipSerializer(friendship).data,
                },
            )
        except Exception:  # noqa: BLE001
            logger.exception("Échec de la notification WS d'acceptation d'ami")

        return Response(FriendshipSerializer(friendship).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Reject a friend request."""
        try:
            friendship = Friendship.objects.get(
                id=pk,
                to_user=request.user,
                status=FriendshipStatus.PENDING,
            )
        except Friendship.DoesNotExist:
            return Response(
                {"error": "Demande introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        friendship.status = FriendshipStatus.REJECTED
        friendship.save()
        return Response({"message": "Demande refusée."})

    @action(detail=True, methods=["delete"])
    def remove(self, request, pk=None):
        """Remove a friend."""
        try:
            friendship = Friendship.objects.get(
                Q(id=pk)
                & (Q(from_user=request.user) | Q(to_user=request.user))
                & Q(status=FriendshipStatus.ACCEPTED)
            )
        except Friendship.DoesNotExist:
            return Response(
                {"error": "Amitié introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        friendship.delete()
        return Response({"message": "Ami supprimé."})
