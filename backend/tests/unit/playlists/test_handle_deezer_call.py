"""Tests unitaires du décorateur handle_deezer_call."""

from unittest.mock import MagicMock, patch

from apps.playlists.decorators import handle_deezer_call
from apps.playlists.deezer_service import DeezerAPIError
from tests.base import BaseUnitTest


class TestHandleDeezerCall(BaseUnitTest):
    """Vérifie le décorateur de gestion d'appels Deezer."""

    def get_target_class(self):
        return handle_deezer_call

    @patch("apps.playlists.decorators.EXTERNAL_API_REQUESTS_TOTAL")
    def test_success_increments_metric(self, mock_metric):
        @handle_deezer_call("search")
        def my_view():
            return "ok"

        result = my_view()
        assert result == "ok"
        mock_metric.labels.assert_called_once_with(service="deezer", endpoint="search")
        mock_metric.labels.return_value.inc.assert_called_once()

    @patch("apps.playlists.decorators.EXTERNAL_API_REQUESTS_TOTAL")
    def test_deezer_error_returns_503(self, mock_metric):
        @handle_deezer_call("tracks")
        def my_view():
            raise DeezerAPIError("API down")

        result = my_view()
        assert result.status_code == 503
        assert "API down" in str(result.data)

    @patch("apps.playlists.decorators.EXTERNAL_API_REQUESTS_TOTAL")
    def test_preserves_function_name(self, mock_metric):
        @handle_deezer_call("test")
        def original_name():
            return "ok"

        assert original_name.__name__ == "original_name"
