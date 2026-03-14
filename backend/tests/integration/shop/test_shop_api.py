"""Tests d'intégration de l'API Shop."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import ShopItemFactory, UserFactory


class TestShopItemList(BaseAPIIntegrationTest):
    """Vérifie la liste des articles de la boutique."""

    def get_base_url(self):
        return "/api/shop/items/"

    def test_list_items(self):
        ShopItemFactory(is_available=True)
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert len(resp.data["results"]) >= 1

    def test_list_unauthenticated(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 401)


class TestShopPurchase(BaseAPIIntegrationTest):
    """Vérifie l'achat d'un article."""

    def get_base_url(self):
        return "/api/shop/items/purchase/"

    def test_purchase_insufficient_coins(self):
        item = ShopItemFactory(cost=1000, is_available=True)
        user = UserFactory(coins_balance=0)
        client = self.get_auth_client(user)
        resp = client.post(
            self.get_base_url(),
            {"item_id": str(item.id), "quantity": 1},  # type: ignore[attr-defined]
            format="json",
        )
        self.assert_status(resp, 402)

    def test_purchase_success(self):
        item = ShopItemFactory(cost=10, is_available=True)
        user = UserFactory(coins_balance=100)
        client = self.get_auth_client(user)
        resp = client.post(
            self.get_base_url(),
            {"item_id": str(item.id), "quantity": 1},  # type: ignore[attr-defined]
            format="json",
        )
        self.assert_status(resp, 201)


class TestShopSummary(BaseAPIIntegrationTest):
    """Vérifie le résumé de la boutique."""

    def get_base_url(self):
        return "/api/shop/items/summary/"

    def test_get_summary(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert "user_balance" in resp.data


class TestInventoryList(BaseAPIIntegrationTest):
    """Vérifie l'inventaire de l'utilisateur."""

    def get_base_url(self):
        return "/api/shop/inventory/"

    def test_list_inventory(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)

    def test_inventory_unauthenticated(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 401)
