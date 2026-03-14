
"""Tests unitaires de BonusService.resolve_round_number."""

from unittest.mock import MagicMock

from apps.shop.services import BonusActivationError, BonusService
from tests.base import BaseUnitTest


class TestResolveRoundNumber(BaseUnitTest):
    """Vérifie la résolution du numéro de round pour les bonus."""

    def get_target_class(self):
        return BonusService

    def setup_method(self):
        self.service = BonusService()

    def test_normal_bonus_with_active_round(self):
        current_round = MagicMock(round_number=3)
        game = MagicMock()
        game.rounds.filter.return_value.first.return_value = current_round
        rn, cr = self.service.resolve_round_number(game, "double_points")
        assert rn == 3
        assert cr is current_round

    def test_normal_bonus_no_active_round(self):
        game = MagicMock()
        game.rounds.filter.return_value.first.return_value = None
        rn, cr = self.service.resolve_round_number(game, "double_points")
        assert rn is None
        assert cr is None

    def test_fog_bonus_next_round(self):
        current_round = MagicMock(round_number=3)
        game = MagicMock()
        game.rounds.filter.return_value.first.return_value = current_round
        rn, cr = self.service.resolve_round_number(game, "fog")
        assert rn == 4

    def test_fog_bonus_no_round_raises(self):
        game = MagicMock()
        game.rounds.filter.return_value.first.return_value = None
        try:
            self.service.resolve_round_number(game, "fog")
            pytest.fail("Expected BonusActivationError")
        except BonusActivationError:
            pass

    def test_joker_no_round_raises(self):
        game = MagicMock()
        game.rounds.filter.return_value.first.return_value = None
        try:
            self.service.resolve_round_number(game, "joker")
            pytest.fail("Expected BonusActivationError")
        except BonusActivationError:
            pass
