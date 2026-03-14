"""Tests unitaires du PrometheusMetricsMiddleware."""

from unittest.mock import MagicMock, patch

from apps.core.middleware import PrometheusMetricsMiddleware
from tests.base import BaseUnitTest


class TestPrometheusMetricsMiddleware(BaseUnitTest):
    """Vérifie le middleware Prometheus."""

    def get_target_class(self):
        return PrometheusMetricsMiddleware

    @patch("apps.core.middleware.HTTP_REQUESTS_TOTAL")
    @patch("apps.core.middleware.HTTP_REQUESTS_IN_PROGRESS")
    @patch("apps.core.middleware.HTTP_REQUEST_DURATION_SECONDS")
    def test_excluded_paths_bypass(self, mock_dur, mock_progress, mock_total):
        response = MagicMock(status_code=200)
        mw = PrometheusMetricsMiddleware(get_response=lambda r: response)
        request = MagicMock()
        request.path = "/api/health/"
        result = mw(request)
        assert result == response
        mock_progress.labels.assert_not_called()

    @patch("apps.core.middleware.HTTP_REQUESTS_TOTAL")
    @patch("apps.core.middleware.HTTP_REQUESTS_IN_PROGRESS")
    @patch("apps.core.middleware.HTTP_REQUEST_DURATION_SECONDS")
    def test_tracks_normal_request(self, mock_dur, mock_progress, mock_total):
        response = MagicMock(status_code=200)
        mw = PrometheusMetricsMiddleware(get_response=lambda r: response)
        request = MagicMock()
        request.path = "/api/games/"
        request.method = "GET"
        mw(request)
        mock_progress.labels.assert_called()
        mock_total.labels.assert_called()
