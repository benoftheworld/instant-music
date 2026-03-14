
"""Tests unitaires du RegisterSerializer."""

from unittest.mock import patch

from apps.authentication.serializers import RegisterSerializer
from tests.base import BaseSerializerUnitTest


class TestRegisterSerializer(BaseSerializerUnitTest):
    """Vérifie la validation du serializer d'inscription."""

    def get_serializer_class(self):
        return RegisterSerializer

    def _valid_data(self):
        return {
            "username": "testuser",
            "email": "test@example.com",
            "password": "SecureP@ss123!",
            "password2": "SecureP@ss123!",
            "accept_privacy_policy": True,
        }

    # ── Champs ──────────────────────────────────────────────────────

    def test_fields(self):
        serializer = RegisterSerializer()
        expected = {
            "username",
            "email",
            "password",
            "password2",
            "accept_privacy_policy",
        }
        assert set(serializer.fields.keys()) == expected

    def test_password_write_only(self):
        serializer = RegisterSerializer()
        assert serializer.fields["password"].write_only is True

    def test_password2_write_only(self):
        serializer = RegisterSerializer()
        assert serializer.fields["password2"].write_only is True

    # ── Validation accept_privacy_policy ────────────────────────────

    def test_privacy_policy_false_calls_validator(self):
        serializer = RegisterSerializer()
        from rest_framework import serializers as drf

        try:
            serializer.validate_accept_privacy_policy(False)
            pytest.fail("Should have raised")
        except drf.ValidationError:
            pass

    def test_privacy_policy_true_passes(self):
        serializer = RegisterSerializer()
        assert serializer.validate_accept_privacy_policy(True) is True

    # ── Validation email unicité ────────────────────────────────────

    @patch("apps.authentication.serializers.User")
    @patch("apps.authentication.serializers.hash_email")
    def test_duplicate_email_rejected(self, mock_hash, mock_user):
        mock_hash.return_value = "hashed"
        mock_user.objects.filter.return_value.exists.return_value = True
        serializer = RegisterSerializer()
        from rest_framework import serializers as drf

        try:
            serializer.validate_email("test@example.com")
            pytest.fail("Should have raised")
        except drf.ValidationError:
            pass

    # ── Validation passwords match ──────────────────────────────────

    def test_validate_passwords_match(self):
        serializer = RegisterSerializer()
        attrs = {"password": "abc", "password2": "abc"}
        result = serializer.validate(attrs)
        assert result == attrs

    def test_validate_passwords_differ(self):
        serializer = RegisterSerializer()
        from rest_framework import serializers as drf

        try:
            serializer.validate({"password": "abc", "password2": "xyz"})
            pytest.fail("Should have raised")
        except drf.ValidationError as e:
            assert "password" in str(e.detail)
