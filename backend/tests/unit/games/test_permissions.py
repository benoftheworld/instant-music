"""Tests unitaires de la permission IsGameHost."""

from unittest.mock import MagicMock

from apps.games.permissions import IsGameHost
from tests.base import BaseUnitTest


class TestIsGameHost(BaseUnitTest):
    """Vérifie que seul l'hôte peut effectuer des actions."""

    def get_target_class(self):
        return IsGameHost

    def _get_permission(self):
        return IsGameHost()

    def test_host_allowed(self):
        perm = self._get_permission()
        user = MagicMock()
        request = MagicMock()
        request.user = user
        game = MagicMock()
        game.host = user
        assert perm.has_object_permission(request, None, game) is True

    def test_non_host_denied(self):
        perm = self._get_permission()
        request = MagicMock()
        request.user = MagicMock()
        game = MagicMock()
        game.host = MagicMock()
        assert perm.has_object_permission(request, None, game) is False

    def test_message(self):
        perm = self._get_permission()
        assert "hôte" in perm.message
