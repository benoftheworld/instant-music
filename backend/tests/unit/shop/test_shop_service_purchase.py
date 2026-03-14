"""Tests unitaires de ShopService.purchase."""

from unittest.mock import MagicMock, patch

import pytest

from apps.shop.services import (
    ItemNotAvailableError,
    ShopService,
)
from tests.base import BaseUnitTest


class TestShopServicePurchase(BaseUnitTest):
    """Vérifie l'achat d'articles en boutique."""

    def get_target_class(self):
        return ShopService

    def setup_method(self):
        self.service = ShopService()

    @patch("apps.shop.services.ShopItem")
    def test_item_not_found_raises(self, mock_item):
        from apps.shop.models import ShopItem

        mock_item.DoesNotExist = ShopItem.DoesNotExist
        mock_item.objects.select_for_update.return_value.get.side_effect = (
            ShopItem.DoesNotExist
        )
        try:
            self.service.purchase.__wrapped__(self.service, MagicMock(), "id1", 1)
            pytest.fail("Expected ItemNotAvailableError")
        except ItemNotAvailableError:
            pass

    @patch("apps.shop.services.ShopItem")
    def test_event_only_free_raises(self, mock_item):
        item = MagicMock(is_event_only=True, cost=0, stock=None)
        mock_item.objects.select_for_update.return_value.get.return_value = item
        try:
            self.service.purchase.__wrapped__(self.service, MagicMock(), "id1", 1)
            pytest.fail("Expected ItemNotAvailableError")
        except ItemNotAvailableError:
            pass

    @patch("apps.shop.services.ShopItem")
    def test_insufficient_stock_raises(self, mock_item):
        item = MagicMock(is_event_only=False, cost=10, stock=0)
        mock_item.objects.select_for_update.return_value.get.return_value = item
        try:
            self.service.purchase.__wrapped__(self.service, MagicMock(), "id1", 1)
            pytest.fail("Expected ItemNotAvailableError")
        except ItemNotAvailableError:
            pass
