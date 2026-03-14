"""Tests unitaires de la commande seed_shop."""

from unittest.mock import MagicMock, patch

from tests.base import BaseServiceUnitTest


class TestSeedShopCommand(BaseServiceUnitTest):
    """Vérifie la commande seed_shop."""

    def get_service_module(self):
        from apps.shop.management.commands import seed_shop

        return seed_shop

    def _run(self, **options):
        from apps.shop.management.commands.seed_shop import Command

        cmd = Command()
        cmd.stdout = MagicMock()
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x
        cmd.style.WARNING = lambda x: x
        cmd.handle(**{"force": False, **options})
        return cmd

    @patch("apps.shop.management.commands.seed_shop.ShopItem")
    def test_creates_new_items(self, mock_si):
        mock_obj = MagicMock(name="Joker")
        mock_si.objects.get_or_create.return_value = (mock_obj, True)
        self._run()
        assert mock_si.objects.get_or_create.call_count > 0

    @patch("apps.shop.management.commands.seed_shop.ShopItem")
    def test_skips_existing_items(self, mock_si):
        mock_obj = MagicMock(name="Existing")
        mock_si.objects.get_or_create.return_value = (mock_obj, False)
        self._run()
        mock_obj.save.assert_not_called()

    @patch("apps.shop.management.commands.seed_shop.ShopItem")
    def test_force_updates_existing(self, mock_si):
        mock_obj = MagicMock(name="Existing")
        mock_si.objects.get_or_create.return_value = (mock_obj, False)
        self._run(force=True)
        assert mock_obj.save.call_count > 0

    @patch("apps.shop.management.commands.seed_shop.ShopItem")
    def test_items_include_bonuses_and_physical(self, mock_si):
        from apps.shop.management.commands.seed_shop import BONUS_ITEMS, PHYSICAL_ITEMS

        mock_si.objects.get_or_create.return_value = (MagicMock(), True)
        self._run()
        expected_count = len(BONUS_ITEMS) + len(PHYSICAL_ITEMS)
        assert mock_si.objects.get_or_create.call_count == expected_count

    def test_bonus_items_defined(self):
        from apps.shop.management.commands.seed_shop import BONUS_ITEMS

        assert len(BONUS_ITEMS) >= 7
        for item in BONUS_ITEMS:
            assert "name" in item
            assert "cost" in item
            assert int(item["cost"]) > 0  # type: ignore[call-overload]

    def test_physical_items_defined(self):
        from apps.shop.management.commands.seed_shop import PHYSICAL_ITEMS

        assert len(PHYSICAL_ITEMS) >= 3
        for item in PHYSICAL_ITEMS:
            assert "name" in item
            assert item.get("is_event_only") is True
