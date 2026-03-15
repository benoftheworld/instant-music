"""Serializers for authentication."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers

from apps.users.encryption import hash_email

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )
    password2 = serializers.CharField(write_only=True, required=True)
    accept_privacy_policy = serializers.BooleanField(
        write_only=True,
        required=True,
        help_text="L'utilisateur doit accepter la politique de confidentialité.",
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "password2", "accept_privacy_policy"]

    def validate_username(self, value):
        """Vérifie que le pseudonyme ne dépasse pas 20 caractères."""
        if len(value) > 20:
            raise serializers.ValidationError(
                "Le pseudonyme ne peut pas dépasser 20 caractères."
            )
        return value

    def validate_accept_privacy_policy(self, value):
        """Vérifie que l'utilisateur a accepté la politique de confidentialité."""
        if not value:
            raise serializers.ValidationError(
                "Vous devez accepter la politique de confidentialité"
                " pour créer un compte."
            )
        return value

    def validate_email(self, value):
        """Vérifie la longueur et l'unicité de l'email."""
        if len(value) > 50:
            raise serializers.ValidationError(
                "L'adresse email ne peut pas dépasser 50 caractères."
            )
        if User.objects.filter(email_hash=hash_email(value)).exists():
            raise serializers.ValidationError("Un compte avec cet email existe déjà.")
        return value

    def validate(self, attrs):
        """Validate passwords match."""
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Les mots de passe ne correspondent pas."}  # nosec B105
            )
        return attrs

    def create(self, validated_data):
        """Create new user."""
        validated_data.pop("password2")
        validated_data.pop("accept_privacy_policy")
        user = User.objects.create_user(**validated_data)
        user.privacy_policy_accepted_at = timezone.now()
        user.save(update_fields=["privacy_policy_accepted_at"])
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class PasswordResetRequestSerializer(serializers.Serializer):
    """Demande de réinitialisation de mot de passe par pseudonyme ou email."""

    identifier = serializers.CharField(
        required=True,
        help_text="Pseudonyme ou adresse email du compte.",
    )


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirmation de réinitialisation avec le token reçu par email."""

    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    new_password2 = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        """Validate that the two new passwords match."""
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError(
                {"new_password": "Les mots de passe ne correspondent pas."}  # nosec B105
            )
        return attrs
