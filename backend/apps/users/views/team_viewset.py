"""ViewSet for teams."""

import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import (
    Team,
    TeamJoinRequest,
    TeamJoinRequestStatus,
    TeamMember,
    TeamMemberRole,
    User,
)
from ..serializers import (
    TeamCreateSerializer,
    TeamJoinRequestCreateSerializer,
    TeamJoinRequestSerializer,
    TeamJoinRequestWithTeamSerializer,
    TeamSerializer,
)

logger = logging.getLogger("apps.users.teams")


class TeamViewSet(viewsets.ModelViewSet):
    """ViewSet for teams."""

    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Return teams the user is a member of or all teams for browsing."""
        if self.action == "list":
            return Team.objects.filter(memberships__user=self.request.user)
        return Team.objects.all()

    def create(self, request):
        """Create a new team."""
        serializer = TeamCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            team = Team.objects.create(
                owner=request.user,
                **serializer.validated_data,
            )
            TeamMember.objects.create(
                team=team,
                user=request.user,
                role=TeamMemberRole.OWNER,
            )

        return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def browse(self, request):
        """Browse all teams."""
        teams = Team.objects.all().order_by("-total_points")[:50]
        return Response(TeamSerializer(teams, many=True).data)

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        """Join a team."""
        try:
            team = Team.objects.get(id=pk)
        except Team.DoesNotExist:
            return Response(
                {"error": "Équipe introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = TeamJoinRequestCreateSerializer(
            data=request.data,
            context={"request": request, "team": team},
        )
        serializer.is_valid(raise_exception=True)

        join_request, created = TeamJoinRequest.objects.get_or_create(
            team=team,
            user=request.user,
            defaults={"status": TeamJoinRequestStatus.PENDING},
        )

        if not created:
            if join_request.status == TeamJoinRequestStatus.PENDING:
                return Response(
                    {"error": "Une demande est déjà en cours."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            # APPROVED (user left) or REJECTED: reset to pending
            join_request.status = TeamJoinRequestStatus.PENDING
            join_request.save()

        # Notifier les admins/owner de l'équipe
        try:
            channel_layer = get_channel_layer()
            admin_ids = TeamMember.objects.filter(
                team=team,
                role__in=[TeamMemberRole.OWNER, TeamMemberRole.ADMIN],
            ).values_list("user_id", flat=True)
            request_data = {
                "id": str(join_request.id),
                "team": {"id": str(team.id), "name": team.name},
                "user": {
                    "id": str(request.user.id),
                    "username": request.user.username,
                    "avatar": request.user.avatar.url if getattr(request.user, "avatar", None) else None,
                },
            }
            for admin_id in admin_ids:
                async_to_sync(channel_layer.group_send)(
                    f"notifications_{admin_id}",
                    {"type": "notify.team_join_request", "request": request_data},
                )
        except Exception:  # noqa: BLE001
            logger.exception("Échec de la notification WS team_join_request")

        return Response(
            {"message": "Demande d'adhésion envoyée."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"])
    def my_pending_requests(self, request):
        """Return all pending join requests for teams where the current user is owner/admin."""
        admin_team_ids = TeamMember.objects.filter(
            user=request.user,
            role__in=[TeamMemberRole.OWNER, TeamMemberRole.ADMIN],
        ).values_list("team_id", flat=True)

        pending = TeamJoinRequest.objects.filter(
            team_id__in=admin_team_ids,
            status=TeamJoinRequestStatus.PENDING,
        ).select_related("user", "team")

        return Response(TeamJoinRequestWithTeamSerializer(pending, many=True).data)

    @action(detail=True, methods=["get"])
    def requests(self, request, pk=None):
        """List pending join requests for a team (owner/admin only)."""
        team, membership = self._require_team_admin(request, pk)
        if isinstance(team, Response):
            return team

        pending = TeamJoinRequest.objects.filter(
            team=team, status=TeamJoinRequestStatus.PENDING
        ).select_related("user")
        return Response(TeamJoinRequestSerializer(pending, many=True).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        """Approve a pending join request (owner/admin only)."""
        request_id = request.data.get("request_id")
        if not request_id:
            return Response(
                {"error": "request_id requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        team, membership = self._require_team_admin(request, pk)
        if isinstance(team, Response):
            return team

        try:
            join_request = TeamJoinRequest.objects.get(
                id=request_id,
                team=team,
                status=TeamJoinRequestStatus.PENDING,
            )
        except TeamJoinRequest.DoesNotExist:
            return Response(
                {"error": "Demande introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        with transaction.atomic():
            join_request.status = TeamJoinRequestStatus.APPROVED
            join_request.save()
            TeamMember.objects.create(
                team=team,
                user=join_request.user,
                role=TeamMemberRole.MEMBER,
            )

        logger.info(
            "team_join_approved",
            extra={
                "team_id": str(team.id),
                "user_id": join_request.user.id,
                "approved_by": request.user.id,
            },
        )

        # Notifier l'utilisateur que sa demande a été approuvée
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{join_request.user.id}",
                {
                    "type": "notify.team_join_approved",
                    "approval": {"team": {"id": str(team.id), "name": team.name}},
                },
            )
        except Exception:  # noqa: BLE001
            logger.exception("Échec de la notification WS team_join_approved")

        return Response({"message": "Demande approuvée."})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        """Reject a pending join request (owner/admin only)."""
        request_id = request.data.get("request_id")
        if not request_id:
            return Response(
                {"error": "request_id requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        team, membership = self._require_team_admin(request, pk)
        if isinstance(team, Response):
            return team

        try:
            join_request = TeamJoinRequest.objects.get(
                id=request_id,
                team=team,
                status=TeamJoinRequestStatus.PENDING,
            )
        except TeamJoinRequest.DoesNotExist:
            return Response(
                {"error": "Demande introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        join_request.status = TeamJoinRequestStatus.REJECTED
        join_request.save()

        # Notifier l'utilisateur que sa demande a été refusée
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{join_request.user.id}",
                {
                    "type": "notify.team_join_rejected",
                    "rejection": {"team": {"id": str(team.id), "name": team.name}},
                },
            )
        except Exception:  # noqa: BLE001
            logger.exception("Échec de la notification WS team_join_rejected")

        return Response({"message": "Demande refusée."})

    @action(detail=True, methods=["post"])
    def dissolve(self, request, pk=None):
        """Dissolve a team (owner only): remove all members and delete the team."""
        team, membership = self._get_team_and_membership(request, pk)
        if isinstance(team, Response):
            return team

        if membership.role != TeamMemberRole.OWNER:
            return Response(
                {"error": "Seul le propriétaire peut dissoudre l'équipe."},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            team.memberships.all().delete()
            team.delete()

        logger.info(
            "team_dissolved",
            extra={"team_name": team.name, "owner_id": request.user.id},
        )

        return Response({"message": "Équipe dissoute avec succès."})

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        """Leave a team."""
        try:
            membership = TeamMember.objects.get(team_id=pk, user=request.user)
        except TeamMember.DoesNotExist:
            return Response(
                {"error": "Vous n'êtes pas membre de cette équipe."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if membership.role == TeamMemberRole.OWNER:
            other_members = TeamMember.objects.filter(team_id=pk).exclude(
                user=request.user
            )
            if other_members.exists():
                new_owner = other_members.first()
                new_owner.role = TeamMemberRole.OWNER
                new_owner.save()
                Team.objects.filter(id=pk).update(owner=new_owner.user)
            else:
                Team.objects.filter(id=pk).delete()
                return Response(
                    {"message": "Équipe supprimée car vous étiez le seul membre."}
                )

        membership.delete()
        return Response({"message": "Vous avez quitté l'équipe."})

    @action(detail=True, methods=["patch"])
    def edit(self, request, pk=None):
        """Edit team description and avatar (owner/admin only)."""
        team, membership = self._require_team_admin(request, pk)
        if isinstance(team, Response):
            return team

        description = request.data.get("description")
        if description is not None:
            team.description = description

        if "avatar" in request.FILES:
            team.avatar = request.FILES["avatar"]

        team.save()
        return Response(TeamSerializer(team).data)

    @action(detail=True, methods=["post"])
    def invite(self, request, pk=None):
        """Invite a user to the team (admin/owner only)."""
        team, membership = self._require_team_admin(request, pk)
        if isinstance(team, Response):
            return team

        username = request.data.get("username")
        if not username:
            return Response(
                {"error": "Nom d'utilisateur requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_to_add = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {"error": "Utilisateur introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if TeamMember.objects.filter(team=team, user=user_to_add).exists():
            return Response(
                {"error": "Cet utilisateur est déjà membre."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        TeamMember.objects.create(
            team=team,
            user=user_to_add,
            role=TeamMemberRole.MEMBER,
        )

        return Response({"message": f"{username} a été ajouté à l'équipe."})

    @action(detail=True, methods=["post"])
    def update_member(self, request, pk=None):
        """Update a member's role (owner/admin only)."""
        member_id = request.data.get("member_id")
        role = request.data.get("role")
        if not member_id or not role:
            return Response(
                {"error": "member_id et role requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        team, membership = self._require_team_admin(request, pk)
        if isinstance(team, Response):
            return team

        try:
            member = TeamMember.objects.get(id=member_id, team=team)
        except TeamMember.DoesNotExist:
            return Response(
                {"error": "Membre introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if (
            member.role == TeamMemberRole.OWNER
            and membership.role != TeamMemberRole.OWNER
        ):
            return Response(
                {"error": "Impossible de modifier le rôle du propriétaire."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if role not in [
            TeamMemberRole.ADMIN,
            TeamMemberRole.MEMBER,
            TeamMemberRole.OWNER,
        ]:
            return Response(
                {"error": "Rôle invalide."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_role = member.role
        with transaction.atomic():
            if role == TeamMemberRole.OWNER:
                TeamMember.objects.filter(team=team, role=TeamMemberRole.OWNER).update(
                    role=TeamMemberRole.ADMIN
                )
                team.owner = member.user
                team.save()
            member.role = role
            member.save()

        # Notifier le membre du changement de rôle
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{member.user_id}",
                {
                    "type": "notify.team_role_updated",
                    "role_update": {
                        "team": {"id": str(team.id), "name": team.name},
                        "old_role": old_role,
                        "new_role": role,
                    },
                },
            )
        except Exception:  # noqa: BLE001
            logger.exception("Échec de la notification WS team_role_updated")

        return Response({"message": "Rôle mis à jour."})

    @action(detail=True, methods=["post"])
    def remove_member(self, request, pk=None):
        """Remove a member from team (owner/admin only)."""
        member_id = request.data.get("member_id")
        if not member_id:
            return Response(
                {"error": "member_id requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        team, membership = self._require_team_admin(request, pk)
        if isinstance(team, Response):
            return team

        try:
            member = TeamMember.objects.get(id=member_id, team=team)
        except TeamMember.DoesNotExist:
            return Response(
                {"error": "Membre introuvable."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if member.role == TeamMemberRole.OWNER:
            return Response(
                {"error": "Impossible de supprimer le propriétaire via cette action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        kicked_user_id = member.user_id
        member.delete()

        # Notifier le membre expulsé
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"notifications_{kicked_user_id}",
                {
                    "type": "notify.team_member_kicked",
                    "kick": {"team": {"id": str(team.id), "name": team.name}},
                },
            )
        except Exception:  # noqa: BLE001
            logger.exception("Échec de la notification WS team_member_kicked")

        return Response({"message": "Membre supprimé."})

    # ── Private helpers ──────────────────────────────────────────────────

    def _get_team_and_membership(self, request, pk):
        """Return (team, membership) or a Response on error."""
        try:
            team = Team.objects.get(id=pk)
            membership = TeamMember.objects.get(team=team, user=request.user)
            return team, membership
        except Team.DoesNotExist:
            return (
                Response(
                    {"error": "Équipe introuvable."},
                    status=status.HTTP_404_NOT_FOUND,
                ),
                None,
            )
        except TeamMember.DoesNotExist:
            return (
                Response(
                    {"error": "Permission refusée."},
                    status=status.HTTP_403_FORBIDDEN,
                ),
                None,
            )

    def _require_team_admin(self, request, pk):
        """Return (team, membership) if user is OWNER or ADMIN, else a Response.

        Factorise le pattern répété dans toutes les actions admin d'équipe.
        """
        team, membership = self._get_team_and_membership(request, pk)
        if isinstance(team, Response):
            return team, None

        if membership.role not in [TeamMemberRole.OWNER, TeamMemberRole.ADMIN]:
            return (
                Response(
                    {"error": "Permission refusée."},
                    status=status.HTTP_403_FORBIDDEN,
                ),
                None,
            )
        return team, membership
