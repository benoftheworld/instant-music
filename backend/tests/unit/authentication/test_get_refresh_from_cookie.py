"""Tests unitaires de get_refresh_from_cookie."""

from unittest.mock import MagicMock

from apps.authentication.cookies import REFRESH_COOKIE_NAME, get_refresh_from_cookie
from tests.base import BaseUnitTest


class TestGetRefreshFromCookie(BaseUnitTest):
    """Vérifie l'extraction du token depuis le cookie."""

    def get_target_class(self):
        return get_refresh_from_cookie

    def test_returns_token(self):
        request = MagicMock()
        request.COOKIES = {REFRESH_COOKIE_NAME: "my-token"}
        assert get_refresh_from_cookie(request) == "my-token"

    def test_returns_none_if_missing(self):
        request = MagicMock()
        request.COOKIES = {}
        assert get_refresh_from_cookie(request) is None
