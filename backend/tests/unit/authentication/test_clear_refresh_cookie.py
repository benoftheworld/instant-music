"""Tests unitaires de clear_refresh_cookie."""

from unittest.mock import MagicMock

from apps.authentication.cookies import REFRESH_COOKIE_NAME, clear_refresh_cookie
from tests.base import BaseUnitTest


class TestClearRefreshCookie(BaseUnitTest):
    """Vérifie la suppression du cookie refresh token."""

    def get_target_class(self):
        return clear_refresh_cookie

    def test_deletes_cookie(self):
        response = MagicMock()
        clear_refresh_cookie(response)
        response.delete_cookie.assert_called_once()
        kwargs = response.delete_cookie.call_args[1]
        assert kwargs["key"] == REFRESH_COOKIE_NAME
        assert kwargs["path"] == "/api/auth/"
