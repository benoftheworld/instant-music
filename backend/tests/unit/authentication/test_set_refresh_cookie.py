"""Tests unitaires des utilitaires de cookies JWT."""

from unittest.mock import MagicMock, patch

from apps.authentication.cookies import (
    REFRESH_COOKIE_NAME,
    clear_refresh_cookie,
    get_refresh_from_cookie,
    set_refresh_cookie,
)
from tests.base import BaseUnitTest


class TestSetRefreshCookie(BaseUnitTest):
    """Vérifie la pose du cookie refresh token."""

    def get_target_class(self):
        return set_refresh_cookie

    @patch("apps.authentication.cookies.settings")
    def test_sets_cookie(self, mock_settings):
        from datetime import timedelta
        mock_settings.SIMPLE_JWT = {"REFRESH_TOKEN_LIFETIME": timedelta(days=7)}
        mock_settings.DEBUG = False
        mock_settings.JWT_REFRESH_COOKIE_SECURE = True
        mock_settings.JWT_REFRESH_COOKIE_SAMESITE = "Strict"

        response = MagicMock()
        set_refresh_cookie(response, "my-token")
        response.set_cookie.assert_called_once()
        kwargs = response.set_cookie.call_args[1]
        assert kwargs["key"] == REFRESH_COOKIE_NAME
        assert kwargs["value"] == "my-token"
        assert kwargs["httponly"] is True
        assert kwargs["path"] == "/api/auth/"
