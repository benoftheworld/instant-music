"""Tests unitaires de BonusService.apply_time_bonus."""

from unittest.mock import MagicMock, patch

from apps.games.models import GamePlayer
from apps.shop.services import BonusService
from tests.base import BaseUnitTest


class TestApplyTimeBonus(BaseUnitTest):
    """Vérifie l'ajout de temps bonus au round."""

    def get_target_class(self):
        return BonusService

    def setup_method(self):
        self.service = BonusService()

    @patch.object(GamePlayer.objects, "get", side_effect=GamePlayer.DoesNotExist)
    def test_player_not_found_returns_zero(self, mock_get):
        result = self.service.apply_time_bonus(
            player=MagicMock(), round_obj=MagicMock()
        )
        assert result == 0

    @patch("apps.shop.services.GameBonus")
    @patch.object(GamePlayer.objects, "get")
    def test_no_bonus_returns_zero(self, mock_get, mock_gb):
        mock_get.return_value = MagicMock()
        mock_gb.objects.filter.return_value.exists.return_value = False
        result = self.service.apply_time_bonus(
            player=MagicMock(), round_obj=MagicMock()
        )
        assert result == 0

    @patch("apps.shop.services.GameBonus")
    @patch.object(GamePlayer.objects, "get")
    def test_adds_time_bonus_seconds(self, mock_get, mock_gb):
        mock_get.return_value = MagicMock()
        bonus = MagicMock()
        qs = MagicMock()
        qs.exists.return_value = True
        qs.__iter__ = lambda self: iter([bonus])
        mock_gb.objects.filter.return_value = qs

        round_obj = MagicMock()
        round_obj.duration = 30
        round_obj.round_number = 1
        round_obj.game = MagicMock()

        result = self.service.apply_time_bonus(
            player=MagicMock(), round_obj=round_obj
        )
        assert result == 30 + BonusService.TIME_BONUS_SECONDS
