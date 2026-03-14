"""Tests unitaires du PasswordResetRequestSerializer."""

from apps.authentication.serializers import PasswordResetRequestSerializer
from tests.base import BaseSerializerUnitTest


class TestPasswordResetRequestSerializer(BaseSerializerUnitTest):
    """Vérifie les champs du serializer de demande de reset."""

    def get_serializer_class(self):
        return PasswordResetRequestSerializer

    def test_fields(self):
        serializer = PasswordResetRequestSerializer()
        assert set(serializer.fields.keys()) == {"email"}

    def test_email_required(self):
        serializer = PasswordResetRequestSerializer(data={})
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_invalid_email_rejected(self):
        serializer = PasswordResetRequestSerializer(data={"email": "not-an-email"})
        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_valid_email(self):
        serializer = PasswordResetRequestSerializer(data={"email": "test@example.com"})
        assert serializer.is_valid()
