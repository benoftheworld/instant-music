"""Tests unitaires du StructuredLoggingMiddleware."""

from unittest.mock import MagicMock, patch

from apps.core.logging_middleware import StructuredLoggingMiddleware
from tests.base import BaseUnitTest


class TestStructuredLoggingMiddleware(BaseUnitTest):
    """Vérifie le middleware de logging structuré."""

    def get_target_class(self):
        return StructuredLoggingMiddleware

    def test_adds_request_id(self):
        response = MagicMock(status_code=200)
        response.__setitem__ = MagicMock()
        mw = StructuredLoggingMiddleware(get_response=lambda r: response)
        request = MagicMock()
        request.path = "/api/games/"
        request.method = "GET"
        request.user = MagicMock()
        request.user.is_authenticated = False
        mw(request)
        # Vérifie que X-Request-ID est ajouté
        response.__setitem__.assert_called()
        args = response.__setitem__.call_args_list
        keys = [a[0][0] for a in args]
        assert "X-Request-ID" in keys

    @patch("apps.core.logging_middleware.logger")
    def test_logs_error_for_5xx(self, mock_logger):
        response = MagicMock(status_code=500)
        response.__setitem__ = MagicMock()
        response.get.return_value = "application/json"
        response.content = b'{"error": "server"}'
        mw = StructuredLoggingMiddleware(get_response=lambda r: response)
        request = MagicMock()
        request.path = "/api/games/"
        request.method = "GET"
        request.user = MagicMock()
        request.user.is_authenticated = False
        mw(request)
        mock_logger.error.assert_called_once()

    @patch("apps.core.logging_middleware.logger")
    def test_logs_warning_for_4xx(self, mock_logger):
        response = MagicMock(status_code=404)
        response.__setitem__ = MagicMock()
        response.get.return_value = "text/html"
        mw = StructuredLoggingMiddleware(get_response=lambda r: response)
        request = MagicMock()
        request.path = "/api/games/"
        request.method = "GET"
        request.user = MagicMock()
        request.user.is_authenticated = False
        mw(request)
        mock_logger.warning.assert_called_once()

    @patch("apps.core.logging_middleware.logger")
    def test_logs_info_for_2xx(self, mock_logger):
        response = MagicMock(status_code=200)
        response.__setitem__ = MagicMock()
        mw = StructuredLoggingMiddleware(get_response=lambda r: response)
        request = MagicMock()
        request.path = "/api/games/"
        request.method = "GET"
        request.user = MagicMock()
        request.user.is_authenticated = False
        mw(request)
        mock_logger.info.assert_called_once()
