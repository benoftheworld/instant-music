"""Tests unitaires du LoginSerializer."""

from apps.authentication.serializers import LoginSerializer
from tests.base import BaseSerializerUnitTest


class TestLoginSerializer(BaseSerializerUnitTest):
    """Vérifie les champs du serializer de connexion."""

    def get_serializer_class(self):
        return LoginSerializer

    def test_fields(self):
        serializer = LoginSerializer()
        assert set(serializer.fields.keys()) == {"username", "password"}

    def test_password_write_only(self):
        serializer = LoginSerializer()
        assert serializer.fields["password"].write_only is True

    def test_username_required(self):
        serializer = LoginSerializer(data={"password": "pass"})
        assert not serializer.is_valid()
        assert "username" in serializer.errors

    def test_password_required(self):
        serializer = LoginSerializer(data={"username": "user"})
        assert not serializer.is_valid()
        assert "password" in serializer.errors

    def test_valid_data(self):
        serializer = LoginSerializer(data={"username": "user", "password": "pass"})
        assert serializer.is_valid()
