"""Serialiseurs de la boutique.
"""

from rest_framework import serializers

from .models import GameBonus, ShopItem, UserInventory


class ShopItemSerializer(serializers.ModelSerializer):
    """Sérialiseur public d'un article de la boutique."""

    is_in_stock = serializers.ReadOnlyField()

    class Meta:
        model = ShopItem
        fields = [
            "id",
            "name",
            "description",
            "icon",
            "item_type",
            "bonus_type",
            "cost",
            "is_event_only",
            "stock",
            "is_available",
            "is_in_stock",
            "sort_order",
        ]


class UserInventorySerializer(serializers.ModelSerializer):
    """Sérialiseur de l'inventaire utilisateur."""

    item = ShopItemSerializer(read_only=True)

    class Meta:
        model = UserInventory
        fields = ["id", "item", "quantity", "purchased_at"]


class PurchaseSerializer(serializers.Serializer):
    """Sérialiseur pour l'achat d'un article."""

    item_id = serializers.UUIDField(required=True)
    quantity = serializers.IntegerField(default=1, min_value=1, max_value=10)


class ActivateBonusSerializer(serializers.Serializer):
    """Sérialiseur pour l'activation d'un bonus en partie."""

    bonus_type = serializers.CharField(required=True)
    room_code = serializers.CharField(required=True)


class GameBonusSerializer(serializers.ModelSerializer):
    """Sérialiseur d'un bonus actif en partie."""

    username = serializers.CharField(source="player.user.username", read_only=True)

    class Meta:
        model = GameBonus
        fields = [
            "id",
            "bonus_type",
            "round_number",
            "activated_at",
            "is_used",
            "used_at",
            "username",
        ]
