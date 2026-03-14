"""Tests d'intégration des vues Shop (ShopViewSet + InventoryViewSet)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rest_framework import status

from tests.base import BaseAPIIntegrationTest
from tests.factories import (
    GameBonusFactory,
    GameFactory,
    GamePlayerFactory,
    GameRoundFactory,
    ShopItemFactory,
    UserFactory,
    UserInventoryFactory,
)

SHOP_URL = "/api/shop/items/"
INVENTORY_URL = "/api/shop/inventory/"


# ═══════════════════════════════════════════════════════════════════
#  ShopViewSet
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestShopItemList(BaseAPIIntegrationTest):
    """GET /api/shop/items/ — catalogue."""

    def get_base_url(self):
        return SHOP_URL

    def test_list_items(self, auth_client):
        ShopItemFactory(name="A")
        ShopItemFactory(name="B")
        resp = auth_client.get(SHOP_URL)
        self.assert_status(resp, status.HTTP_200_OK)
        assert len(resp.data) >= 2

    def test_list_items_unauthenticated(self, api_client):
        resp = api_client.get(SHOP_URL)
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.django_db
class TestShopSummary(BaseAPIIntegrationTest):
    """GET /api/shop/items/summary/ — résumé boutique."""

    def get_base_url(self):
        return SHOP_URL

    def test_summary_returns_balance(self, auth_client, user):
        ShopItemFactory()
        resp = auth_client.get(f"{SHOP_URL}summary/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert "user_balance" in resp.data
        assert "total_coins_available" in resp.data
        assert "items_count" in resp.data


@pytest.mark.django_db
class TestShopPurchase(BaseAPIIntegrationTest):
    """POST /api/shop/items/purchase/ — achat."""

    def get_base_url(self):
        return SHOP_URL

    def test_purchase_success(self, auth_client, user):
        item = ShopItemFactory(cost=10)
        user.coins_balance = 100
        user.save(update_fields=["coins_balance"])
        resp = auth_client.post(
            f"{SHOP_URL}purchase/",
            {"item_id": str(item.id), "quantity": 1},  # type: ignore[attr-defined]
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)

    def test_purchase_insufficient_coins(self, auth_client, user):
        item = ShopItemFactory(cost=999)
        user.coins_balance = 0
        user.save(update_fields=["coins_balance"])
        resp = auth_client.post(
            f"{SHOP_URL}purchase/",
            {"item_id": str(item.id), "quantity": 1},  # type: ignore[attr-defined]
            format="json",
        )
        self.assert_status(resp, status.HTTP_402_PAYMENT_REQUIRED)

    def test_purchase_unavailable_item(self, auth_client, user):
        item = ShopItemFactory(is_available=False)
        user.coins_balance = 1000
        user.save(update_fields=["coins_balance"])
        resp = auth_client.post(
            f"{SHOP_URL}purchase/",
            {"item_id": str(item.id), "quantity": 1},  # type: ignore[attr-defined]
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_purchase_missing_fields(self, auth_client):
        resp = auth_client.post(f"{SHOP_URL}purchase/", {}, format="json")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════════
#  InventoryViewSet
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestInventoryList(BaseAPIIntegrationTest):
    """GET /api/shop/inventory/ — inventaire."""

    def get_base_url(self):
        return INVENTORY_URL

    def test_list_inventory(self, auth_client, user):
        item = ShopItemFactory()
        UserInventoryFactory(user=user, item=item, quantity=3)
        resp = auth_client.get(INVENTORY_URL)
        self.assert_status(resp, status.HTTP_200_OK)
        assert len(resp.data) >= 1

    def test_list_inventory_empty(self, auth_client):
        resp = auth_client.get(INVENTORY_URL)
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data == []


@pytest.mark.django_db
class TestInventoryActivate(BaseAPIIntegrationTest):
    """POST /api/shop/inventory/activate/ — activer un bonus."""

    def get_base_url(self):
        return INVENTORY_URL

    def _create_game_with_player_and_round(self, user):
        game = GameFactory(host=user, status="in_progress", bonuses_enabled=True)
        player = GamePlayerFactory(game=game, user=user)
        round_obj = GameRoundFactory(
            game=game,
            round_number=1,
            correct_answer="Song A",
            options=["Song A", "Song B", "Song C", "Song D"],
        )
        return game, player, round_obj

    def test_activate_game_not_found(self, auth_client, user):
        resp = auth_client.post(
            f"{INVENTORY_URL}activate/",
            {"bonus_type": "double_points", "room_code": "ZZZZZZ"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)

    def test_activate_bonuses_disabled(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress", bonuses_enabled=False)
        GamePlayerFactory(game=game, user=user)
        resp = auth_client.post(
            f"{INVENTORY_URL}activate/",
            {"bonus_type": "double_points", "room_code": game.room_code},
            format="json",
        )
        self.assert_status(resp, status.HTTP_403_FORBIDDEN)

    @patch("apps.shop.views.bonus_service")
    def test_activate_resolve_round_error(self, mock_svc, auth_client, user):
        from apps.shop.services import BonusActivationError

        game = GameFactory(host=user, status="in_progress", bonuses_enabled=True)
        GamePlayerFactory(game=game, user=user)
        mock_svc.resolve_round_number.side_effect = BonusActivationError(
            "Aucune manche"
        )
        resp = auth_client.post(
            f"{INVENTORY_URL}activate/",
            {"bonus_type": "double_points", "room_code": game.room_code},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    @patch("channels.layers.get_channel_layer")
    @patch("apps.shop.views.bonus_service")
    def test_activate_fifty_fifty(self, mock_svc, mock_channel, auth_client, user):
        game, player, round_obj = self._create_game_with_player_and_round(user)
        mock_svc.resolve_round_number.return_value = (1, round_obj)
        mock_svc.activate_bonus.return_value = GameBonusFactory.build(
            game=game, player=player, bonus_type="fifty_fifty"
        )
        mock_svc.get_fifty_fifty_exclusions.return_value = ["Song B", "Song C"]
        layer = MagicMock()
        layer.group_send = AsyncMock()
        mock_channel.return_value = layer

        resp = auth_client.post(
            f"{INVENTORY_URL}activate/",
            {"bonus_type": "fifty_fifty", "room_code": game.room_code},
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)
        assert "excluded_options" in resp.data

    @patch("channels.layers.get_channel_layer")
    @patch("apps.shop.views.bonus_service")
    def test_activate_steal_first_player_blocked(
        self, mock_svc, mock_channel, auth_client, user
    ):
        game, player, round_obj = self._create_game_with_player_and_round(user)
        # Player is in first position (no one with higher score)
        mock_svc.resolve_round_number.return_value = (1, round_obj)

        resp = auth_client.post(
            f"{INVENTORY_URL}activate/",
            {"bonus_type": "steal", "room_code": game.room_code},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)
        assert "meneur" in resp.data["detail"]

    @patch("channels.layers.get_channel_layer")
    @patch("apps.shop.views.bonus_service")
    def test_activate_steal_success(self, mock_svc, mock_channel, auth_client, user):
        game, player, round_obj = self._create_game_with_player_and_round(user)
        # Add another player with higher score so current player isn't first
        other = UserFactory()
        GamePlayerFactory(game=game, user=other, score=500)
        player.score = 100
        player.save()

        mock_svc.resolve_round_number.return_value = (1, round_obj)
        mock_svc.activate_bonus.return_value = GameBonusFactory.build(
            game=game, player=player, bonus_type="steal"
        )
        mock_svc.apply_steal_bonus.return_value = 50
        layer = MagicMock()
        layer.group_send = AsyncMock()
        mock_channel.return_value = layer

        resp = auth_client.post(
            f"{INVENTORY_URL}activate/",
            {"bonus_type": "steal", "room_code": game.room_code},
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)
        assert "stolen_points" in resp.data

    @patch("channels.layers.get_channel_layer")
    @patch("apps.shop.views.bonus_service")
    def test_activate_time_bonus(self, mock_svc, mock_channel, auth_client, user):
        game, player, round_obj = self._create_game_with_player_and_round(user)
        mock_svc.resolve_round_number.return_value = (1, round_obj)
        mock_svc.activate_bonus.return_value = GameBonusFactory.build(
            game=game, player=player, bonus_type="time_bonus"
        )
        mock_svc.apply_time_bonus.return_value = 45
        layer = MagicMock()
        layer.group_send = AsyncMock()
        mock_channel.return_value = layer

        resp = auth_client.post(
            f"{INVENTORY_URL}activate/",
            {"bonus_type": "time_bonus", "room_code": game.room_code},
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)
        assert resp.data.get("new_duration") == 45

    @patch("apps.shop.views.bonus_service")
    def test_activate_already_active(self, mock_svc, auth_client, user):
        from apps.shop.services import BonusAlreadyActiveError

        game = GameFactory(host=user, status="in_progress", bonuses_enabled=True)
        GamePlayerFactory(game=game, user=user)
        mock_svc.resolve_round_number.return_value = (1, None)
        mock_svc.activate_bonus.side_effect = BonusAlreadyActiveError("Déjà actif")
        resp = auth_client.post(
            f"{INVENTORY_URL}activate/",
            {"bonus_type": "double_points", "room_code": game.room_code},
            format="json",
        )
        self.assert_status(resp, status.HTTP_409_CONFLICT)

    def test_activate_missing_fields(self, auth_client):
        resp = auth_client.post(f"{INVENTORY_URL}activate/", {}, format="json")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestInventoryGameBonuses(BaseAPIIntegrationTest):
    """GET /api/shop/inventory/game/{room_code}/ — bonus actifs."""

    def get_base_url(self):
        return INVENTORY_URL

    def test_game_bonuses_success(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        player = GamePlayerFactory(game=game, user=user)
        GameBonusFactory(game=game, player=player, is_used=False)
        resp = auth_client.get(f"{INVENTORY_URL}game/{game.room_code}/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert len(resp.data) >= 1

    def test_game_bonuses_not_found(self, auth_client):
        resp = auth_client.get(f"{INVENTORY_URL}game/ZZZZZZ/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)

    def test_game_bonuses_not_player(self, auth_client, user):
        game = GameFactory(status="in_progress")
        resp = auth_client.get(f"{INVENTORY_URL}game/{game.room_code}/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)
