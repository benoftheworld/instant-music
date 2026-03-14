"""Tests unitaires de BonusService.apply_steal_bonus."""

from unittest.mock import MagicMock, patch, call

from apps.shop.services import BonusService
from tests.base import BaseUnitTest


class TestApplyStealBonus(BaseUnitTest):
    """Vérifie la logique du vol de points."""

    def get_target_class(self):
        return BonusService

    def setup_method(self):
        self.service = BonusService()

    @patch("apps.shop.services.GameBonus")
    def test_no_bonus_returns_zero(self, mock_gb):
        mock_gb.objects.filter.return_value.exists.return_value = False
        result = self.service.apply_steal_bonus(
            player=MagicMock(), game=MagicMock(), round_number=1
        )
        assert result == 0

    @patch("apps.games.models.GamePlayer")
    @patch("apps.shop.services.GameBonus")
    def test_no_leader_returns_zero(self, mock_gb, mock_gp):
        steal_qs = MagicMock()
        steal_qs.exists.return_value = True
        bonus = MagicMock()
        steal_qs.__iter__ = lambda self: iter([bonus])
        mock_gb.objects.filter.return_value = steal_qs

        mock_gp.objects.filter.return_value.exclude.return_value.order_by.return_value.first.return_value = None

        result = self.service.apply_steal_bonus(
            player=MagicMock(), game=MagicMock(), round_number=1
        )
        assert result == 0
