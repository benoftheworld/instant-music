"""
Serializers for User models.
"""
from rest_framework import serializers
from django.db.models import Sum
from .models import User, Friendship, FriendshipStatus, Team, TeamMember, TeamMemberRole
from .models import TeamJoinRequest, TeamJoinRequestStatus


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    
    win_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'avatar',
            'total_games_played',
            'total_wins',
            'total_points',
            'win_rate',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'total_games_played',
            'total_wins',
            'total_points',
            'created_at',
            'updated_at',
        ]


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user info for lists."""

    class Meta:
        model = User
        fields = ['id', 'username', 'avatar', 'total_points', 'total_wins']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = ['avatar']


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change endpoint."""
    
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    
    def validate_new_password(self, value):
        """Validate new password."""
        # Add custom password validation here
        if len(value) < 8:
            raise serializers.ValidationError("Le mot de passe doit contenir au moins 8 caractères.")
        return value


# ─── Friendship Serializers ──────────────────────────────────────────────────

class FriendshipSerializer(serializers.ModelSerializer):
    """Serializer for Friendship model."""
    
    from_user = UserMinimalSerializer(read_only=True)
    to_user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = Friendship
        fields = ['id', 'from_user', 'to_user', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'from_user', 'status', 'created_at', 'updated_at']


class FriendshipCreateSerializer(serializers.Serializer):
    """Serializer for creating a friendship request."""
    
    username = serializers.CharField(required=True)
    
    def validate_username(self, value):
        try:
            User.objects.get(username=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("Utilisateur introuvable.")
        return value


# ─── Team Serializers ────────────────────────────────────────────────────────

class TeamMemberSerializer(serializers.ModelSerializer):
    """Serializer for TeamMember."""
    
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = TeamMember
        fields = ['id', 'user', 'role', 'joined_at']


class TeamSerializer(serializers.ModelSerializer):
    """Serializer for Team model."""
    
    owner = UserMinimalSerializer(read_only=True)
    members_list = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()
    # Aggregate member stats to provide up-to-date team statistics
    total_games = serializers.SerializerMethodField()
    total_wins = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()
    
    class Meta:
        model = Team
        fields = [
            'id', 'name', 'description', 'avatar', 'owner',
            'members_list', 'member_count',
            'total_games', 'total_wins', 'total_points',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'total_games', 'total_wins', 'total_points', 'created_at', 'updated_at']
    
    def get_members_list(self, obj):
        memberships = obj.memberships.select_related('user').all()[:10]
        return TeamMemberSerializer(memberships, many=True).data
    
    def get_member_count(self, obj):
        return obj.memberships.count()

    def get_total_points(self, obj):
        # Sum total_points of users who are members
        return obj.members.aggregate(s=Sum('total_points'))['s'] or 0

    def get_total_games(self, obj):
        return obj.members.aggregate(s=Sum('total_games_played'))['s'] or 0

    def get_total_wins(self, obj):
        return obj.members.aggregate(s=Sum('total_wins'))['s'] or 0


class TeamCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a team."""
    
    class Meta:
        model = Team
        fields = ['name', 'description', 'avatar']


class TeamJoinRequestSerializer(serializers.ModelSerializer):
    """Serializer for listing join requests."""

    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = TeamJoinRequest
        fields = ['id', 'user', 'status', 'created_at']
        read_only_fields = ['id', 'user', 'status', 'created_at']


class TeamJoinRequestCreateSerializer(serializers.Serializer):
    """Serializer to create a join request (no body required)."""

    def validate(self, attrs):
        request = self.context.get('request')
        team = self.context.get('team')

        # Check if already member
        if TeamMember.objects.filter(team=team, user=request.user).exists():
            raise serializers.ValidationError('Vous êtes déjà membre de cette équipe.')

        # Check if request already exists
        if TeamJoinRequest.objects.filter(team=team, user=request.user).exists():
            existing = TeamJoinRequest.objects.get(team=team, user=request.user)
            if existing.status == TeamJoinRequestStatus.PENDING:
                raise serializers.ValidationError('Une demande est déjà en cours.')
            elif existing.status == TeamJoinRequestStatus.APPROVED:
                raise serializers.ValidationError('Votre demande a déjà été approuvée.')

        return attrs

