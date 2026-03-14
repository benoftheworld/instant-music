"""Tests du JwtWebSocketMiddleware."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.base import BaseServiceUnitTest


class TestExtractToken(BaseServiceUnitTest):
    """Vérifie l'extraction du token depuis le query string."""

    def get_service_module(self):
        import apps.authentication.jwt_ws_middleware
        return apps.authentication.jwt_ws_middleware

    def test_extracts_token(self):
        from apps.authentication.jwt_ws_middleware import JwtWebSocketMiddleware

        scope = {"query_string": b"token=abc123"}
        result = JwtWebSocketMiddleware._extract_token(scope)
        assert result == "abc123"

    def test_no_token_returns_none(self):
        from apps.authentication.jwt_ws_middleware import JwtWebSocketMiddleware

        scope = {"query_string": b""}
        result = JwtWebSocketMiddleware._extract_token(scope)
        assert result is None

    def test_no_query_string_returns_none(self):
        from apps.authentication.jwt_ws_middleware import JwtWebSocketMiddleware

        scope = {}
        result = JwtWebSocketMiddleware._extract_token(scope)
        assert result is None

    def test_multiple_params(self):
        from apps.authentication.jwt_ws_middleware import JwtWebSocketMiddleware

        scope = {"query_string": b"foo=bar&token=mytoken&baz=qux"}
        result = JwtWebSocketMiddleware._extract_token(scope)
        assert result == "mytoken"


class TestJwtMiddlewareCall(BaseServiceUnitTest):
    """Vérifie le comportement global du middleware."""

    def get_service_module(self):
        import apps.authentication.jwt_ws_middleware
        return apps.authentication.jwt_ws_middleware
    @pytest.mark.asyncio
    async def test_non_websocket_passthrough(self):
        from apps.authentication.jwt_ws_middleware import JwtWebSocketMiddleware

        mock_inner = AsyncMock()
        middleware = JwtWebSocketMiddleware(mock_inner)
        scope = {"type": "http", "query_string": b""}
        await middleware(scope, AsyncMock(), AsyncMock())
        mock_inner.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_token_closes_4003(self):
        from apps.authentication.jwt_ws_middleware import JwtWebSocketMiddleware

        mock_inner = AsyncMock()
        middleware = JwtWebSocketMiddleware(mock_inner)
        mock_send = AsyncMock()
        scope = {"type": "websocket", "query_string": b"", "path": "/ws/test/"}
        await middleware(scope, AsyncMock(), mock_send)
        mock_send.assert_called_once_with(
            {"type": "websocket.close", "code": 4003}
        )
        mock_inner.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_token_closes_4003(self):
        from apps.authentication.jwt_ws_middleware import JwtWebSocketMiddleware

        mock_inner = AsyncMock()
        middleware = JwtWebSocketMiddleware(mock_inner)
        mock_send = AsyncMock()
        scope = {
            "type": "websocket",
            "query_string": b"token=invalid_token",
            "path": "/ws/test/",
        }
        await middleware(scope, AsyncMock(), mock_send)
        mock_send.assert_called_once_with(
            {"type": "websocket.close", "code": 4003}
        )
