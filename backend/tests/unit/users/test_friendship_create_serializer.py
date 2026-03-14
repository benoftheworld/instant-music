"""Tests unitaires de FriendshipCreateSerializer.validate_username."""

from unittest.mock import MagicMock, patch

from tests.base import BaseUnitTest


class TestFriendshipCreateSerializerValidation(BaseUnitTest):
    """Vérifie la validation du username dans FriendshipCreateSerializer."""

    def get_target_class(self):
        from apps.users.serializers.friendship_serializer import FriendshipCreateSerializer
        return FriendshipCreateSerializer

    @patch("apps.users.serializers.friendship_serializer.User")
    def test_valid_username(self, mock_user_class):
        from apps.users.serializers.friendship_serializer import FriendshipCreateSerializer
        mock_user_class.objects.get.return_value = MagicMock()
        ser = FriendshipCreateSerializer()
        result = ser.validate_username("alice")
        assert result == "alice"

    @patch("apps.users.serializers.friendship_serializer.User")
    def test_invalid_username_raises(self, mock_user_class):
        from rest_framework import serializers as drf_ser
        from apps.users.serializers.friendship_serializer import FriendshipCreateSerializer
        from apps.users.models import User
        mock_user_class.DoesNotExist = User.DoesNotExist
        mock_user_class.objects.get.side_effect = User.DoesNotExist
        ser = FriendshipCreateSerializer()
        try:
            ser.validate_username("unknown")
            assert False, "Expected ValidationError"
        except drf_ser.ValidationError:
            pass
