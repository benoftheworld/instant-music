"""Tests de l'application boutique.
"""

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.shop.models import BonusType, ItemType, ShopItem, UserInventory


@pytest.mark.django_db
class TestShopItems:
    """Tests du catalogue de la boutique."""

    def setup_method(self):
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.item_bonus = ShopItem.objects.create(
            name="Double Points",
            description="Double les points",
            item_type=ItemType.BONUS,
            bonus_type=BonusType.DOUBLE_POINTS,
            cost=50,
        )
        self.item_physical = ShopItem.objects.create(
            name="T-shirt",
            description="T-shirt event",
            item_type=ItemType.PHYSICAL,
            cost=0,
            is_event_only=True,
        )

    def test_list_shop_items(self):
        response = self.client.get("/api/shop/items/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) >= 2

    def test_shop_summary(self):
        response = self.client.get("/api/shop/items/summary/")
        assert response.status_code == status.HTTP_200_OK
        assert "user_balance" in response.data
        assert "total_coins_available" in response.data

    def test_purchase_item_success(self):
        self.user.coins_balance = 100
        self.user.save()

        response = self.client.post(
            "/api/shop/items/purchase/",
            {"item_id": str(self.item_bonus.id), "quantity": 1},
        )
        assert response.status_code == status.HTTP_201_CREATED
        self.user.refresh_from_db()
        assert self.user.coins_balance == 50

        inv = UserInventory.objects.get(user=self.user, item=self.item_bonus)
        assert inv.quantity == 1

    def test_purchase_insufficient_coins(self):
        self.user.coins_balance = 10
        self.user.save()

        response = self.client.post(
            "/api/shop/items/purchase/",
            {"item_id": str(self.item_bonus.id), "quantity": 1},
        )
        assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED

    def test_purchase_event_only_physical_blocked(self):
        self.user.coins_balance = 1000
        self.user.save()

        response = self.client.post(
            "/api/shop/items/purchase/",
            {"item_id": str(self.item_physical.id), "quantity": 1},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_inventory_list(self):
        UserInventory.objects.create(user=self.user, item=self.item_bonus, quantity=2)
        response = self.client.get("/api/shop/inventory/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["quantity"] == 2
