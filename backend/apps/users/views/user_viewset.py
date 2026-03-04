"""ViewSet for User model."""

import json

from django.contrib.auth import update_session_auth_hash
from django.db import transaction
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)

from ..models import User
from ..models.team_member import TeamMember
from ..serializers import (
    ChangePasswordSerializer,
    UserMinimalSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
)
from apps.achievements.models import UserAchievement
from apps.games.models import GameAnswer
from apps.shop.models import UserInventory


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter queryset based on user."""
        if self.action == "list":
            if self.request.user.is_staff:
                return User.objects.all()
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()

    @action(detail=False, methods=["get", "patch"])
    def me(self, request):
        """Get or update current user profile."""
        if request.method == "GET":
            serializer = UserSerializer(
                request.user, context={"request": request}
            )
            return Response(serializer.data)

        serializer = UserProfileUpdateSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                UserSerializer(request.user, context={"request": request}).data
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def change_password(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user

            if not user.check_password(
                serializer.validated_data["old_password"]
            ):
                return Response(
                    {"old_password": "Mot de passe incorrect."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data["new_password"])
            user.save()
            update_session_auth_hash(request, user)

            return Response(
                {"message": "Mot de passe modifié avec succès."},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["delete"])
    def delete_account(self, request):
        """Delete user account and all associated data (GDPR)."""
        user = request.user
        # Invalider tous les tokens avant suppression pour déconnecter les sessions actives
        for token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=token)
        with transaction.atomic():
            user.delete()

        return Response(
            {"message": "Compte supprimé avec succès."},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def search(self, request):
        """Search users by username."""
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response([])

        users = (
            User.objects.filter(username__icontains=query)
            .exclude(id=request.user.id)
            .exclude(is_superuser=True)
        )[:10]

        serializer = UserMinimalSerializer(users, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def export_data(self, request):
        """Export toutes les données personnelles de l'utilisateur (RGPD art. 20)."""
        user = request.user
        data = {
            "exported_at": timezone.now().isoformat(),
            "profile": {
                "username": user.username,
                "email": user.email,
                "created_at": user.created_at.isoformat(),
                "total_games_played": user.total_games_played,
                "total_wins": user.total_wins,
                "total_points": user.total_points,
                "coins": getattr(user, "coins", None),
            },
            "game_participations": [
                {
                    "room_code": gp.game.room_code,
                    "mode": gp.game.mode,
                    "score": gp.score,
                    "rank": gp.rank,
                    "played_at": (
                        gp.game.started_at.isoformat() if gp.game.started_at else None
                    ),
                }
                for gp in user.game_participations.select_related("game").order_by(
                    "-joined_at"
                )
            ],
            "game_answers": [
                {
                    "room_code": ans.round.game.room_code,
                    "round_number": ans.round.round_number,
                    "answer": ans.answer,
                    "is_correct": ans.is_correct,
                    "points_earned": ans.points_earned,
                    "response_time": ans.response_time,
                    "answered_at": (
                        ans.answered_at.isoformat() if ans.answered_at else None
                    ),
                }
                for ans in GameAnswer.objects.filter(
                    player__user=user
                ).select_related("round__game").order_by("-answered_at")[:500]
            ],
            "achievements": [
                {
                    "name": ua.achievement.name,
                    "description": ua.achievement.description,
                    "unlocked_at": ua.unlocked_at.isoformat(),
                }
                for ua in UserAchievement.objects.filter(
                    user=user
                ).select_related("achievement")
            ],
            "teams": [
                {
                    "team_name": tm.team.name,
                    "role": tm.role,
                    "joined_at": tm.joined_at.isoformat() if hasattr(tm, "joined_at") else None,
                }
                for tm in TeamMember.objects.filter(
                    user=user
                ).select_related("team")
            ],
            "inventory": [
                {
                    "item_name": inv.item.name if hasattr(inv, "item") else str(inv),
                    "quantity": getattr(inv, "quantity", None),
                    "acquired_at": inv.acquired_at.isoformat() if hasattr(inv, "acquired_at") else None,
                }
                for inv in UserInventory.objects.filter(user=user)
            ],
            "friends": [
                {
                    "username": f.to_user.username,
                    "since": f.updated_at.isoformat(),
                }
                for f in user.friendships_sent.filter(
                    status="accepted"
                ).select_related("to_user")
            ]
            + [
                {
                    "username": f.from_user.username,
                    "since": f.updated_at.isoformat(),
                }
                for f in user.friendships_received.filter(
                    status="accepted"
                ).select_related("from_user")
            ],
        }
        response = HttpResponse(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type="application/json",
        )
        response["Content-Disposition"] = (
            'attachment; filename="mes-donnees-instantmusic.json"'
        )
        return response
