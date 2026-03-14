"""Team serializers."""

from rest_framework import serializers

from ..models import (
    Team,
    TeamJoinRequest,
    TeamJoinRequestStatus,
    TeamMember,
)
from .user_serializer import UserMinimalSerializer


class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for TeamMember."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = TeamMember
        fields = ["id", "user", "role", "joined_at"]


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model."""

    owner = UserMinimalSerializer(read_only=True)
    members_list = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = [
            "id",
            "name",
            "description",
            "avatar",
            "owner",
            "members_list",
            "member_count",
            "total_games",
            "total_wins",
            "total_points",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "owner",
            "total_games",
            "total_wins",
            "total_points",
            "created_at",
            "updated_at",
        ]

    def get_members_list(self, obj):
        """Return up to 10 serialized team memberships."""
        memberships = obj.memberships.select_related("user").all()[:10]
        return TeamMemberSerializer(memberships, many=True).data

    def get_member_count(self, obj):
        """Return the total number of team memberships."""
        return obj.memberships.count()


class TeamCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a team."""

    class Meta:
        model = Team
        fields = ["name", "description", "avatar"]


class TeamJoinRequestSerializer(serializers.ModelSerializer):
    """Serializer for listing join requests."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = TeamJoinRequest
        fields = ["id", "user", "status", "created_at"]
        read_only_fields = ["id", "user", "status", "created_at"]


class TeamJoinRequestWithTeamSerializer(serializers.ModelSerializer):
    """Serializer for listing join requests with team info (for my_pending_requests)."""

    user = UserMinimalSerializer(read_only=True)
    team = serializers.SerializerMethodField()

    class Meta:
        model = TeamJoinRequest
        fields = ["id", "user", "team", "status", "created_at"]
        read_only_fields = ["id", "user", "team", "status", "created_at"]

    def get_team(self, obj):
        """Return the team ID and name as a dict."""
        return {"id": str(obj.team_id), "name": obj.team.name}


class TeamJoinRequestCreateSerializer(serializers.Serializer):
    """Serializer to create a join request (no body required)."""

    def validate(self, attrs):
        """Validate that the user is not already a member or has a pending request."""
        request = self.context.get("request")
        team = self.context.get("team")

        if TeamMember.objects.filter(team=team, user=request.user).exists():
            raise serializers.ValidationError("Vous êtes déjà membre de cette équipe.")

        try:
            existing = TeamJoinRequest.objects.get(team=team, user=request.user)
        except TeamJoinRequest.DoesNotExist:
            return attrs

        if existing.status == TeamJoinRequestStatus.PENDING:
            raise serializers.ValidationError("Une demande est déjà en cours.")
        # APPROVED but no membership means the user left — allow re-request
        # REJECTED: allow a new request

        return attrs
