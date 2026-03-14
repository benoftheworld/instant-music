"""Tests unitaires de l'ActivateBonusSerializer."""

from apps.shop.serializers import ActivateBonusSerializer
from tests.base import BaseSerializerUnitTest


class TestActivateBonusSerializer(BaseSerializerUnitTest):
    """Vérifie la validation du serializer d'activation de bonus."""

    def get_serializer_class(self):
        return ActivateBonusSerializer

    def test_fields(self):
        serializer = ActivateBonusSerializer()
        assert set(serializer.fields.keys()) == {"bonus_type", "room_code"}

    def test_bonus_type_required(self):
        serializer = ActivateBonusSerializer(data={"room_code": "ABC123"})
        assert not serializer.is_valid()
        assert "bonus_type" in serializer.errors

    def test_room_code_required(self):
        serializer = ActivateBonusSerializer(data={"bonus_type": "double_points"})
        assert not serializer.is_valid()
        assert "room_code" in serializer.errors

    def test_valid_data(self):
        serializer = ActivateBonusSerializer(
            data={"bonus_type": "double_points", "room_code": "ABC123"}
        )
        assert serializer.is_valid()
