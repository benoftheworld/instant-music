"""Tests unitaires du ChangePasswordSerializer."""

from unittest.mock import patch

from apps.users.serializers.user_serializer import ChangePasswordSerializer
from tests.base import BaseSerializerUnitTest


class TestChangePasswordSerializer(BaseSerializerUnitTest):
    """Vérifie la validation du changement de mot de passe."""

    def get_serializer_class(self):
        return ChangePasswordSerializer

    def test_fields(self):
        serializer = ChangePasswordSerializer()
        assert set(serializer.fields.keys()) == {"old_password", "new_password"}

    def test_old_password_required(self):
        serializer = ChangePasswordSerializer(data={"new_password": "new"})
        assert not serializer.is_valid()
        assert "old_password" in serializer.errors

    def test_new_password_required(self):
        serializer = ChangePasswordSerializer(data={"old_password": "old"})
        assert not serializer.is_valid()
        assert "new_password" in serializer.errors

    @patch("apps.users.serializers.user_serializer.validate_password")
    def test_valid_data(self, mock_validate):
        mock_validate.return_value = None
        serializer = ChangePasswordSerializer(
            data={"old_password": "old", "new_password": "SecureP@ss123!"}
        )
        assert serializer.is_valid()
