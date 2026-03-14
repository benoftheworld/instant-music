"""Tests unitaires de la permission IsOwnerOrReadOnly."""

from unittest.mock import MagicMock

from apps.users.permissions import IsOwnerOrReadOnly
from tests.base import BaseUnitTest


class TestIsOwnerOrReadOnly(BaseUnitTest):
    """Vérifie la logique de permission propriétaire vs lecture seule."""

    def get_target_class(self):
        return IsOwnerOrReadOnly

    def _get_permission(self):
        return IsOwnerOrReadOnly()

    # ── Méthodes sûres (GET, HEAD, OPTIONS) ─────────────────────────

    def test_safe_method_get_allows(self):
        perm = self._get_permission()
        request = MagicMock()
        request.method = "GET"
        assert perm.has_object_permission(request, None, MagicMock()) is True

    def test_safe_method_head_allows(self):
        perm = self._get_permission()
        request = MagicMock()
        request.method = "HEAD"
        assert perm.has_object_permission(request, None, MagicMock()) is True

    def test_safe_method_options_allows(self):
        perm = self._get_permission()
        request = MagicMock()
        request.method = "OPTIONS"
        assert perm.has_object_permission(request, None, MagicMock()) is True

    # ── Méthodes d'écriture ─────────────────────────────────────────

    def test_put_owner_allows(self):
        perm = self._get_permission()
        user = MagicMock()
        request = MagicMock()
        request.method = "PUT"
        request.user = user
        assert perm.has_object_permission(request, None, user) is True

    def test_put_non_owner_denies(self):
        perm = self._get_permission()
        request = MagicMock()
        request.method = "PUT"
        request.user = MagicMock()
        assert perm.has_object_permission(request, None, MagicMock()) is False

    def test_patch_owner_allows(self):
        perm = self._get_permission()
        user = MagicMock()
        request = MagicMock()
        request.method = "PATCH"
        request.user = user
        assert perm.has_object_permission(request, None, user) is True

    def test_delete_non_owner_denies(self):
        perm = self._get_permission()
        request = MagicMock()
        request.method = "DELETE"
        request.user = MagicMock()
        assert perm.has_object_permission(request, None, MagicMock()) is False
