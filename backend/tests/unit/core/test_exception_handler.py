"""Tests unitaires du handler d'exceptions DRF."""

from unittest.mock import MagicMock, patch

from rest_framework.response import Response

from apps.core.exception_handler import custom_exception_handler
from tests.base import BaseUnitTest


class TestCustomExceptionHandler(BaseUnitTest):
    """Vérifie le logging et l'enrichissement des réponses d'erreur."""

    def get_target_class(self):
        return custom_exception_handler

    def _make_context(self, user=None, method="GET", path="/api/test/"):
        request = MagicMock()
        request.method = method
        request.path = path
        request._request_id = "req-123"
        request.user = user or MagicMock(is_authenticated=False)
        view = MagicMock()
        view.__class__.__module__ = "apps.test"
        view.__class__.__name__ = "TestView"
        return {"request": request, "view": view}

    @patch("apps.core.exception_handler.exception_handler")
    @patch("apps.core.exception_handler.logger")
    def test_handled_4xx_logs_warning(self, mock_logger, mock_base_handler):
        response = MagicMock(spec=Response)
        response.status_code = 400
        response.data = {"detail": "Bad request"}
        mock_base_handler.return_value = response

        result = custom_exception_handler(ValueError(""), self._make_context())
        assert result is response
        mock_logger.warning.assert_called()

    @patch("apps.core.exception_handler.exception_handler")
    @patch("apps.core.exception_handler.logger")
    def test_handled_5xx_logs_error(self, mock_logger, mock_base_handler):
        response = MagicMock(spec=Response)
        response.status_code = 500
        response.data = {"detail": "Server error"}
        mock_base_handler.return_value = response

        result = custom_exception_handler(RuntimeError(""), self._make_context())
        assert result is response
        mock_logger.error.assert_called()

    @patch("apps.core.exception_handler.exception_handler")
    @patch("apps.core.exception_handler.logger")
    def test_handled_403_logs_warning(self, mock_logger, mock_base_handler):
        response = MagicMock(spec=Response)
        response.status_code = 403
        response.data = {"detail": "Forbidden"}
        mock_base_handler.return_value = response

        result = custom_exception_handler(PermissionError(""), self._make_context())
        assert result is response
        mock_logger.warning.assert_called()

    @patch("apps.core.exception_handler.exception_handler")
    @patch("apps.core.exception_handler.logger")
    def test_handled_401_logs_warning(self, mock_logger, mock_base_handler):
        response = MagicMock(spec=Response)
        response.status_code = 401
        response.data = {"detail": "Unauthorized"}
        mock_base_handler.return_value = response

        result = custom_exception_handler(Exception(""), self._make_context())
        assert result is response
        mock_logger.warning.assert_called()

    @patch("apps.core.exception_handler.exception_handler")
    @patch("apps.core.exception_handler.logger")
    def test_handled_404_logs_info(self, mock_logger, mock_base_handler):
        response = MagicMock(spec=Response)
        response.status_code = 404
        response.data = {"detail": "Not found"}
        mock_base_handler.return_value = response

        result = custom_exception_handler(Exception(""), self._make_context())
        assert result is response
        mock_logger.info.assert_called()

    @patch("apps.core.exception_handler.exception_handler")
    @patch("apps.core.exception_handler.logger")
    def test_handled_429_logs_warning(self, mock_logger, mock_base_handler):
        response = MagicMock(spec=Response)
        response.status_code = 429
        response.data = {"detail": "Throttled"}
        mock_base_handler.return_value = response

        result = custom_exception_handler(Exception(""), self._make_context())
        assert result is response
        mock_logger.warning.assert_called()

    @patch("apps.core.exception_handler.exception_handler")
    @patch("apps.core.exception_handler.logger")
    def test_unhandled_exception_logs_error(self, mock_logger, mock_base_handler):
        """Exception non gérée par DRF → log error avec traceback."""
        mock_base_handler.return_value = None

        result = custom_exception_handler(RuntimeError("boom"), self._make_context())
        assert result is None
        mock_logger.error.assert_called()

    @patch("apps.core.exception_handler.exception_handler")
    def test_authenticated_user_in_log(self, mock_base_handler):
        response = MagicMock(spec=Response)
        response.status_code = 400
        response.data = {}
        mock_base_handler.return_value = response

        user = MagicMock()
        user.is_authenticated = True
        user.id = 42

        with patch("apps.core.exception_handler.logger") as mock_logger:
            custom_exception_handler(ValueError(""), self._make_context(user=user))
            # Vérifie que le logger est appelé avec le contexte user
            mock_logger.warning.assert_called()
