"""
Serializers for authentication.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2']
    
    def validate(self, attrs):
        """Validate passwords match."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Les mots de passe ne correspondent pas."}
            )
        return attrs
    
    def create(self, validated_data):
        """Create new user."""
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""
    
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class GoogleOAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth."""
    
    token = serializers.CharField(required=True)
