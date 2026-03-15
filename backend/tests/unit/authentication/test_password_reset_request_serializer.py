"""Tests unitaires du PasswordResetRequestSerializer."""

from apps.authentication.serializers import PasswordResetRequestSerializer
from tests.base import BaseSerializerUnitTest


class TestPasswordResetRequestSerializer(BaseSerializerUnitTest):
    """Vérifie les champs du serializer de demande de reset par pseudonyme."""

    def get_serializer_class(self):
        return PasswordResetRequestSerializer

    def test_fields(self):
        serializer = PasswordResetRequestSerializer()
        assert set(serializer.fields.keys()) == {"username"}

    def test_username_required(self):
        serializer = PasswordResetRequestSerializer(data={})
        assert not serializer.is_valid()
        assert "username" in serializer.errors

    def test_username_too_long_rejected(self):
        serializer = PasswordResetRequestSerializer(data={"username": "a" * 21})
        assert not serializer.is_valid()
        assert "username" in serializer.errors

    def test_valid_username(self):
        serializer = PasswordResetRequestSerializer(data={"username": "monpseudo"})
        assert serializer.is_valid()
