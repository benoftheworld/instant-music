"""Tests unitaires du PurchaseSerializer."""

from apps.shop.serializers import PurchaseSerializer
from tests.base import BaseSerializerUnitTest


class TestPurchaseSerializer(BaseSerializerUnitTest):
    """Vérifie la validation du serializer d'achat."""

    def get_serializer_class(self):
        return PurchaseSerializer

    def test_fields(self):
        serializer = PurchaseSerializer()
        assert set(serializer.fields.keys()) == {"item_id", "quantity"}

    def test_item_id_required(self):
        serializer = PurchaseSerializer(data={"quantity": 1})
        assert not serializer.is_valid()
        assert "item_id" in serializer.errors

    def test_quantity_default(self):
        serializer = PurchaseSerializer()
        assert serializer.fields["quantity"].default == 1

    def test_quantity_min_value(self):
        serializer = PurchaseSerializer(
            data={"item_id": "550e8400-e29b-41d4-a716-446655440000", "quantity": 0}
        )
        assert not serializer.is_valid()
        assert "quantity" in serializer.errors

    def test_quantity_max_value(self):
        serializer = PurchaseSerializer(
            data={"item_id": "550e8400-e29b-41d4-a716-446655440000", "quantity": 11}
        )
        assert not serializer.is_valid()
        assert "quantity" in serializer.errors

    def test_valid_data(self):
        serializer = PurchaseSerializer(
            data={"item_id": "550e8400-e29b-41d4-a716-446655440000", "quantity": 5}
        )
        assert serializer.is_valid()

    def test_invalid_uuid(self):
        serializer = PurchaseSerializer(data={"item_id": "not-a-uuid", "quantity": 1})
        assert not serializer.is_valid()
        assert "item_id" in serializer.errors
