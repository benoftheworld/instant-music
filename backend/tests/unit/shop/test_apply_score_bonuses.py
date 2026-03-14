"""Tests unitaires de BonusService.apply_score_bonuses."""

from unittest.mock import MagicMock, patch

from apps.shop.services import BonusService
from tests.base import BaseUnitTest


class TestApplyScoreBonuses(BaseUnitTest):
    """Vérifie l'application des bonus de score."""

    def get_target_class(self):
        return BonusService

    def setup_method(self):
        self.service = BonusService()

    @patch("apps.shop.services.GameBonus")
    def test_incorrect_answer_returns_base(self, mock_gb):
        pts, bonuses = self.service.apply_score_bonuses(
            player=MagicMock(),
            round_number=1,
            base_points=100,
            is_correct=False,
            game=MagicMock(),
        )
        assert pts == 100
        assert bonuses == []

    @patch("apps.shop.services.GameBonus")
    def test_no_active_bonus(self, mock_gb):
        mock_gb.objects.filter.return_value.select_for_update.return_value = []
        pts, bonuses = self.service.apply_score_bonuses(
            player=MagicMock(),
            round_number=1,
            base_points=100,
            is_correct=True,
            game=MagicMock(),
        )
        assert pts == 100
        assert bonuses == []

    @patch("apps.shop.services.GameBonus")
    def test_double_points_bonus(self, mock_gb):
        from apps.shop.models import BonusType

        bonus = MagicMock(bonus_type=BonusType.DOUBLE_POINTS)
        mock_gb.objects.filter.return_value.select_for_update.return_value = [bonus]
        pts, bonuses = self.service.apply_score_bonuses(
            player=MagicMock(),
            round_number=1,
            base_points=100,
            is_correct=True,
            game=MagicMock(),
        )
        assert pts == 200
        assert BonusType.DOUBLE_POINTS in bonuses

    @patch("apps.games.services.SCORE_BASE_POINTS", 1000)
    @patch("apps.shop.services.GameBonus")
    def test_max_points_bonus(self, mock_gb):
        from apps.shop.models import BonusType

        bonus = MagicMock(bonus_type=BonusType.MAX_POINTS)
        mock_gb.objects.filter.return_value.select_for_update.return_value = [bonus]
        pts, bonuses = self.service.apply_score_bonuses(
            player=MagicMock(),
            round_number=1,
            base_points=50,
            is_correct=True,
            game=MagicMock(),
        )
        assert pts == 1000
        assert BonusType.MAX_POINTS in bonuses
