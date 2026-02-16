"""
Serializers for User models.
"""
from rest_framework import serializers
from .models import User


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
            'bio',
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


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user profile."""
    
    class Meta:
        model = User
        fields = ['bio', 'avatar']


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
