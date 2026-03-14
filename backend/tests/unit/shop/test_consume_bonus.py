"""Tests unitaires de BonusService.consume_bonus."""

from unittest.mock import MagicMock

from apps.shop.services import BonusService
from tests.base import BaseUnitTest


class TestConsumeBonus(BaseUnitTest):
    """Vérifie le marquage d'un bonus comme consommé."""

    def get_target_class(self):
        return BonusService

    def test_sets_used_and_timestamp(self):
        service = BonusService()
        game_bonus = MagicMock()
        service.consume_bonus(game_bonus)
        assert game_bonus.is_used is True
        assert game_bonus.used_at is not None
        game_bonus.save.assert_called_once_with(update_fields=["is_used", "used_at"])
