"""
Views for achievements.
"""
from rest_framework import generics, permissions
from rest_framework.response import Response
from .models import Achievement, UserAchievement
from .serializers import AchievementSerializer, UserAchievementSerializer


class AchievementListView(generics.ListAPIView):
    """List all achievements with unlock status for the current user."""
    
    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        return Achievement.objects.all().order_by('condition_type', 'condition_value')


class UserAchievementListView(generics.ListAPIView):
    """List achievements unlocked by the current user."""
    
    serializer_class = UserAchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserAchievement.objects.filter(
            user=self.request.user
        ).select_related('achievement').order_by('-unlocked_at')


class UserAchievementsByUserView(generics.ListAPIView):
    """List achievements unlocked by a specific user (public)."""
    
    serializer_class = UserAchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        return UserAchievement.objects.filter(
            user_id=user_id
        ).select_related('achievement').order_by('-unlocked_at')
