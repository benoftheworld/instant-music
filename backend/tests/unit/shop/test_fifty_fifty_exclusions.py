"""Tests unitaires de BonusService.get_fifty_fifty_exclusions."""

from unittest.mock import MagicMock, patch

from apps.shop.services import BonusService
from tests.base import BaseUnitTest


class TestFiftyFiftyExclusions(BaseUnitTest):
    """Vérifie la sélection des réponses à masquer pour le 50/50."""

    def get_target_class(self):
        return BonusService

    def setup_method(self):
        self.service = BonusService()

    @patch("apps.shop.services.GameBonus")
    def test_no_bonus_returns_empty(self, mock_gb):
        mock_gb.objects.filter.return_value.exists.return_value = False
        result = self.service.get_fifty_fifty_exclusions(
            player=MagicMock(),
            round_number=1,
            options=["A", "B", "C", "D"],
            correct_answer="A",
        )
        assert result == []

    @patch("apps.shop.services.random")
    @patch("apps.shop.services.GameBonus")
    def test_returns_two_wrong_answers(self, mock_gb, mock_random):
        mock_gb.objects.filter.return_value.exists.return_value = True
        bonus = MagicMock()
        mock_gb.objects.filter.return_value.__iter__ = lambda self: iter([bonus])
        mock_random.sample.return_value = ["B", "C"]
        result = self.service.get_fifty_fifty_exclusions(
            player=MagicMock(),
            round_number=1,
            options=["A", "B", "C", "D"],
            correct_answer="A",
        )
        assert len(result) == 2
        assert "A" not in result

    @patch("apps.shop.services.random")
    @patch("apps.shop.services.GameBonus")
    def test_fewer_wrong_answers(self, mock_gb, mock_random):
        mock_gb.objects.filter.return_value.exists.return_value = True
        bonus = MagicMock()
        mock_gb.objects.filter.return_value.__iter__ = lambda self: iter([bonus])
        mock_random.sample.return_value = ["B"]
        result = self.service.get_fifty_fifty_exclusions(
            player=MagicMock(), round_number=1, options=["A", "B"], correct_answer="A"
        )
        assert len(result) == 1
