
"""Tests unitaires du PasswordResetConfirmSerializer."""

from rest_framework import serializers as drf

from apps.authentication.serializers import PasswordResetConfirmSerializer
from tests.base import BaseSerializerUnitTest


class TestPasswordResetConfirmSerializer(BaseSerializerUnitTest):
    """Vérifie la validation du serializer de confirmation de reset."""

    def get_serializer_class(self):
        return PasswordResetConfirmSerializer

    def test_fields(self):
        serializer = PasswordResetConfirmSerializer()
        expected = {"uid", "token", "new_password", "new_password2"}
        assert set(serializer.fields.keys()) == expected

    def test_new_password_write_only(self):
        serializer = PasswordResetConfirmSerializer()
        assert serializer.fields["new_password"].write_only is True

    def test_new_password2_write_only(self):
        serializer = PasswordResetConfirmSerializer()
        assert serializer.fields["new_password2"].write_only is True

    def test_validate_passwords_match(self):
        serializer = PasswordResetConfirmSerializer()
        attrs = {
            "uid": "abc",
            "token": "tok",
            "new_password": "SecureP@ss",
            "new_password2": "SecureP@ss",
        }
        result = serializer.validate(attrs)
        assert result == attrs

    def test_validate_passwords_differ(self):
        serializer = PasswordResetConfirmSerializer()
        attrs = {
            "uid": "abc",
            "token": "tok",
            "new_password": "SecureP@ss",
            "new_password2": "Different",
        }
        try:
            serializer.validate(attrs)
            pytest.fail("Should have raised")
        except drf.ValidationError as e:
            assert "new_password" in str(e.detail)

    def test_uid_required(self):
        serializer = PasswordResetConfirmSerializer(
            data={"token": "t", "new_password": "p", "new_password2": "p"}
        )
        assert not serializer.is_valid()
        assert "uid" in serializer.errors

    def test_token_required(self):
        serializer = PasswordResetConfirmSerializer(
            data={"uid": "u", "new_password": "p", "new_password2": "p"}
        )
        assert not serializer.is_valid()
        assert "token" in serializer.errors
