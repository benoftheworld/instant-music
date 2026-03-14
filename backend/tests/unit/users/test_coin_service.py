"""Tests unitaires du service de gestion des pièces."""

from unittest.mock import MagicMock, patch

import pytest

from apps.users.coin_service import InsufficientCoinsError, get_balance
from tests.base import BaseServiceUnitTest


class TestCoinService(BaseServiceUnitTest):
    """Vérifie les opérations atomiques de crédit/débit de pièces."""

    def get_service_module(self):
        import apps.users.coin_service

        return apps.users.coin_service

    # ── add_coins ───────────────────────────────────────────────────

    @patch("apps.users.coin_service.get_balance", return_value=150)
    @patch("apps.users.coin_service.User")
    @patch("apps.users.coin_service.transaction")
    def test_add_coins_positive(self, mock_tx, mock_user_cls, mock_balance):
        from apps.users.coin_service import add_coins

        result = add_coins.__wrapped__(user_id=1, amount=50, reason="test")
        mock_user_cls.objects.filter.return_value.update.assert_called_once()
        assert result == 150

    @patch("apps.users.coin_service.get_balance", return_value=100)
    @patch("apps.users.coin_service.User")
    @patch("apps.users.coin_service.transaction")
    def test_add_coins_zero_returns_balance(self, mock_tx, mock_user_cls, mock_balance):
        """amount=0 → pas d'update, retourne le solde actuel."""
        from apps.users.coin_service import add_coins

        result = add_coins.__wrapped__(user_id=1, amount=0, reason="noop")
        mock_user_cls.objects.filter.return_value.update.assert_not_called()
        assert result == 100

    @patch("apps.users.coin_service.get_balance", return_value=100)
    @patch("apps.users.coin_service.User")
    @patch("apps.users.coin_service.transaction")
    def test_add_coins_negative_returns_balance(
        self, mock_tx, mock_user_cls, mock_balance
    ):
        """Amount négatif → pas d'update, retourne le solde actuel."""
        from apps.users.coin_service import add_coins

        result = add_coins.__wrapped__(user_id=1, amount=-10, reason="negative")
        mock_user_cls.objects.filter.return_value.update.assert_not_called()
        assert result == 100

    # ── deduct_coins ────────────────────────────────────────────────

    @patch("apps.users.coin_service.get_balance", return_value=50)
    @patch("apps.users.coin_service.User")
    @patch("apps.users.coin_service.transaction")
    def test_deduct_coins_sufficient(self, mock_tx, mock_user_cls, mock_balance):
        from apps.users.coin_service import deduct_coins

        mock_user = MagicMock()
        mock_user.coins_balance = 100
        mock_user_cls.objects.select_for_update.return_value.get.return_value = (
            mock_user
        )
        result = deduct_coins.__wrapped__(user_id=1, amount=50, reason="achat")
        mock_user_cls.objects.filter.return_value.update.assert_called_once()
        assert result == 50

    @patch("apps.users.coin_service.User")
    @patch("apps.users.coin_service.transaction")
    def test_deduct_coins_insufficient_raises(self, mock_tx, mock_user_cls):
        from apps.users.coin_service import deduct_coins

        mock_user = MagicMock()
        mock_user.coins_balance = 10
        mock_user_cls.objects.select_for_update.return_value.get.return_value = (
            mock_user
        )
        with pytest.raises(InsufficientCoinsError, match="Solde insuffisant"):
            deduct_coins.__wrapped__(user_id=1, amount=50, reason="achat")

    @patch("apps.users.coin_service.get_balance", return_value=100)
    @patch("apps.users.coin_service.User")
    @patch("apps.users.coin_service.transaction")
    def test_deduct_coins_zero_returns_balance(
        self, mock_tx, mock_user_cls, mock_balance
    ):
        from apps.users.coin_service import deduct_coins

        result = deduct_coins.__wrapped__(user_id=1, amount=0, reason="noop")
        assert result == 100

    @patch("apps.users.coin_service.get_balance", return_value=100)
    @patch("apps.users.coin_service.User")
    @patch("apps.users.coin_service.transaction")
    def test_deduct_coins_negative_returns_balance(
        self, mock_tx, mock_user_cls, mock_balance
    ):
        from apps.users.coin_service import deduct_coins

        result = deduct_coins.__wrapped__(user_id=1, amount=-5, reason="negative")
        assert result == 100

    # ── get_balance ─────────────────────────────────────────────────

    @patch("apps.users.coin_service.User")
    def test_get_balance_returns_value(self, mock_user_cls):
        mock_user_cls.objects.filter.return_value.values_list.return_value.first.return_value = (  # noqa: E501
            200
        )
        result = get_balance(user_id=1)
        assert result == 200

    @patch("apps.users.coin_service.User")
    def test_get_balance_none_returns_zero(self, mock_user_cls):
        """User inexistant → retourne 0."""
        mock_user_cls.objects.filter.return_value.values_list.return_value.first.return_value = (  # noqa: E501
            None
        )
        result = get_balance(user_id=999)
        assert result == 0
