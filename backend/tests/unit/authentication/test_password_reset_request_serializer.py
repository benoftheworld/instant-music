"""Tests unitaires du PasswordResetRequestSerializer."""

from apps.authentication.serializers import PasswordResetRequestSerializer
from tests.base import BaseSerializerUnitTest


class TestPasswordResetRequestSerializer(BaseSerializerUnitTest):
    """Vérifie les champs du serializer de demande de reset par pseudonyme ou email."""

    def get_serializer_class(self):
        return PasswordResetRequestSerializer

    def test_fields(self):
        serializer = PasswordResetRequestSerializer()
        assert set(serializer.fields.keys()) == {"identifier"}

    def test_identifier_required(self):
        serializer = PasswordResetRequestSerializer(data={})
        assert not serializer.is_valid()
        assert "identifier" in serializer.errors

    def test_valid_username(self):
        serializer = PasswordResetRequestSerializer(data={"identifier": "monpseudo"})
        assert serializer.is_valid()

    def test_valid_email(self):
        serializer = PasswordResetRequestSerializer(data={"identifier": "user@exemple.com"})
        assert serializer.is_valid()
