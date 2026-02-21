"""
Serializers for achievements.
"""
from rest_framework import serializers
from .models import Achievement, UserAchievement


class AchievementSerializer(serializers.ModelSerializer):
    """Serializer for Achievement model."""
    
    unlocked = serializers.SerializerMethodField()
    unlocked_at = serializers.SerializerMethodField()
    
    class Meta:
        model = Achievement
        fields = [
            'id',
            'name',
            'description',
            'icon',
            'points',
            'condition_type',
            'condition_value',
            'unlocked',
            'unlocked_at',
        ]
    
    def get_unlocked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return UserAchievement.objects.filter(
                user=request.user,
                achievement=obj
            ).exists()
        return False
    
    def get_unlocked_at(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            ua = UserAchievement.objects.filter(
                user=request.user,
                achievement=obj
            ).first()
            if ua:
                return ua.unlocked_at.isoformat()
        return None


class UserAchievementSerializer(serializers.ModelSerializer):
    """Serializer for UserAchievement model."""
    
    achievement = AchievementSerializer(read_only=True)
    
    class Meta:
        model = UserAchievement
        fields = ['id', 'achievement', 'unlocked_at']
