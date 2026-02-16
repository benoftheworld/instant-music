"""
Views for User app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import update_session_auth_hash
from django.db.models import Q
from django.db import transaction

from .models import User, Friendship, FriendshipStatus, Team, TeamMember, TeamMemberRole
from .serializers import (
    UserSerializer,
    UserMinimalSerializer,
    UserProfileUpdateSerializer,
    ChangePasswordSerializer,
    FriendshipSerializer,
    FriendshipCreateSerializer,
    TeamSerializer,
    TeamCreateSerializer,
    TeamMemberSerializer,
)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User model."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter queryset based on user."""
        if self.action == 'list':
            # Only admins can list all users
            if self.request.user.is_staff:
                return User.objects.all()
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()
    
    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Get or update current user profile."""
        if request.method == 'GET':
            serializer = UserSerializer(request.user, context={'request': request})
            return Response(serializer.data)
        
        elif request.method == 'PATCH':
            serializer = UserProfileUpdateSerializer(
                request.user,
                data=request.data,
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(UserSerializer(request.user, context={'request': request}).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change user password."""
        serializer = ChangePasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            user = request.user
            
            # Check old password
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {'old_password': 'Mot de passe incorrect.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Set new password
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Update session to prevent logout
            update_session_auth_hash(request, user)
            
            return Response(
                {'message': 'Mot de passe modifié avec succès.'},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def delete_account(self, request):
        """Delete user account and all associated data (GDPR)."""
        user = request.user
        
        with transaction.atomic():
            # Delete all user data - cascades will handle related models
            user.delete()
        
        return Response(
            {'message': 'Compte supprimé avec succès.'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Search users by username."""
        query = request.query_params.get('q', '').strip()
        if len(query) < 2:
            return Response([])
        
        users = User.objects.filter(
            username__icontains=query
        ).exclude(
            id=request.user.id
        )[:10]
        
        serializer = UserMinimalSerializer(users, many=True)
        return Response(serializer.data)


class FriendshipViewSet(viewsets.ViewSet):
    """ViewSet for managing friendships."""
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """List all friends (accepted friendships)."""
        user = request.user
        friendships = Friendship.objects.filter(
            Q(from_user=user, status=FriendshipStatus.ACCEPTED) |
            Q(to_user=user, status=FriendshipStatus.ACCEPTED)
        ).select_related('from_user', 'to_user')
        
        # Extract friend users
        friends = []
        for f in friendships:
            friend = f.to_user if f.from_user == user else f.from_user
            friends.append({
                'friendship_id': f.id,
                'user': UserMinimalSerializer(friend).data,
                'since': f.updated_at
            })
        
        return Response(friends)
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """List pending friend requests received."""
        requests = Friendship.objects.filter(
            to_user=request.user,
            status=FriendshipStatus.PENDING
        ).select_related('from_user', 'to_user')
        
        return Response(FriendshipSerializer(requests, many=True).data)
    
    @action(detail=False, methods=['get'])
    def sent(self, request):
        """List friend requests sent."""
        requests = Friendship.objects.filter(
            from_user=request.user,
            status=FriendshipStatus.PENDING
        ).select_related('from_user', 'to_user')
        
        return Response(FriendshipSerializer(requests, many=True).data)
    
    @action(detail=False, methods=['post'])
    def send_request(self, request):
        """Send a friend request."""
        serializer = FriendshipCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        username = serializer.validated_data['username']
        to_user = User.objects.get(username=username)
        
        if to_user == request.user:
            return Response(
                {'error': 'Vous ne pouvez pas vous ajouter vous-même.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if friendship already exists
        existing = Friendship.objects.filter(
            Q(from_user=request.user, to_user=to_user) |
            Q(from_user=to_user, to_user=request.user)
        ).first()
        
        if existing:
            if existing.status == FriendshipStatus.ACCEPTED:
                return Response({'error': 'Vous êtes déjà amis.'}, status=status.HTTP_400_BAD_REQUEST)
            elif existing.status == FriendshipStatus.PENDING:
                return Response({'error': 'Une demande est déjà en cours.'}, status=status.HTTP_400_BAD_REQUEST)
        
        friendship = Friendship.objects.create(
            from_user=request.user,
            to_user=to_user,
            status=FriendshipStatus.PENDING
        )
        
        return Response(FriendshipSerializer(friendship).data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a friend request."""
        try:
            friendship = Friendship.objects.get(
                id=pk,
                to_user=request.user,
                status=FriendshipStatus.PENDING
            )
        except Friendship.DoesNotExist:
            return Response({'error': 'Demande introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        
        friendship.status = FriendshipStatus.ACCEPTED
        friendship.save()
        
        return Response(FriendshipSerializer(friendship).data)
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Reject a friend request."""
        try:
            friendship = Friendship.objects.get(
                id=pk,
                to_user=request.user,
                status=FriendshipStatus.PENDING
            )
        except Friendship.DoesNotExist:
            return Response({'error': 'Demande introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        
        friendship.status = FriendshipStatus.REJECTED
        friendship.save()
        
        return Response({'message': 'Demande refusée.'})
    
    @action(detail=True, methods=['delete'])
    def remove(self, request, pk=None):
        """Remove a friend."""
        try:
            friendship = Friendship.objects.get(
                Q(id=pk) &
                (Q(from_user=request.user) | Q(to_user=request.user)) &
                Q(status=FriendshipStatus.ACCEPTED)
            )
        except Friendship.DoesNotExist:
            return Response({'error': 'Amitié introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        
        friendship.delete()
        return Response({'message': 'Ami supprimé.'})


class TeamViewSet(viewsets.ModelViewSet):
    """ViewSet for teams."""
    
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None  # Disable pagination for teams
    
    def get_queryset(self):
        """Return teams the user is a member of or all teams for browsing."""
        if self.action == 'list':
            # Show user's teams
            return Team.objects.filter(memberships__user=self.request.user)
        return Team.objects.all()
    
    def create(self, request):
        """Create a new team."""
        serializer = TeamCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            team = Team.objects.create(
                owner=request.user,
                **serializer.validated_data
            )
            TeamMember.objects.create(
                team=team,
                user=request.user,
                role=TeamMemberRole.OWNER
            )
        
        return Response(TeamSerializer(team).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def browse(self, request):
        """Browse all teams."""
        teams = Team.objects.all().order_by('-total_points')[:50]
        return Response(TeamSerializer(teams, many=True).data)
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a team."""
        try:
            team = Team.objects.get(id=pk)
        except Team.DoesNotExist:
            return Response({'error': 'Équipe introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        
        if TeamMember.objects.filter(team=team, user=request.user).exists():
            return Response({'error': 'Vous êtes déjà membre de cette équipe.'}, status=status.HTTP_400_BAD_REQUEST)
        
        TeamMember.objects.create(
            team=team,
            user=request.user,
            role=TeamMemberRole.MEMBER
        )
        
        return Response(TeamSerializer(team).data)
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a team."""
        try:
            membership = TeamMember.objects.get(team_id=pk, user=request.user)
        except TeamMember.DoesNotExist:
            return Response({'error': 'Vous n\'êtes pas membre de cette équipe.'}, status=status.HTTP_404_NOT_FOUND)
        
        if membership.role == TeamMemberRole.OWNER:
            # Transfer ownership or delete team
            other_members = TeamMember.objects.filter(team_id=pk).exclude(user=request.user)
            if other_members.exists():
                new_owner = other_members.first()
                new_owner.role = TeamMemberRole.OWNER
                new_owner.save()
                Team.objects.filter(id=pk).update(owner=new_owner.user)
            else:
                # Delete team if no other members
                Team.objects.filter(id=pk).delete()
                return Response({'message': 'Équipe supprimée car vous étiez le seul membre.'})
        
        membership.delete()
        return Response({'message': 'Vous avez quitté l\'équipe.'})
    
    @action(detail=True, methods=['post'])
    def invite(self, request, pk=None):
        """Invite a user to the team (admin/owner only)."""
        try:
            team = Team.objects.get(id=pk)
            membership = TeamMember.objects.get(team=team, user=request.user)
        except (Team.DoesNotExist, TeamMember.DoesNotExist):
            return Response({'error': 'Équipe introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        
        if membership.role not in [TeamMemberRole.OWNER, TeamMemberRole.ADMIN]:
            return Response({'error': 'Permission refusée.'}, status=status.HTTP_403_FORBIDDEN)
        
        username = request.data.get('username')
        if not username:
            return Response({'error': 'Nom d\'utilisateur requis.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user_to_add = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
        
        if TeamMember.objects.filter(team=team, user=user_to_add).exists():
            return Response({'error': 'Cet utilisateur est déjà membre.'}, status=status.HTTP_400_BAD_REQUEST)
        
        TeamMember.objects.create(
            team=team,
            user=user_to_add,
            role=TeamMemberRole.MEMBER
        )
        
        return Response({'message': f'{username} a été ajouté à l\'équipe.'})

