"""Tests unitaires des health checks."""

from unittest.mock import MagicMock, patch

from apps.core.health import health_check
from tests.base import BaseUnitTest


class TestHealthCheck(BaseUnitTest):
    """Vérifie le health check principal."""

    def get_target_class(self):
        return health_check

    @patch("apps.core.health.cache")
    @patch("apps.core.health.connection")
    def test_healthy(self, mock_conn, mock_cache):
        """DB + cache OK → 200."""
        mock_cache.get.return_value = "ok"
        request = MagicMock()
        response = health_check(request)
        assert response.status_code == 200

    @patch("apps.core.health.cache")
    @patch("apps.core.health.connection")
    def test_db_down(self, mock_conn, mock_cache):
        """DB KO → 503."""
        mock_conn.ensure_connection.side_effect = Exception("DB down")
        mock_cache.get.return_value = "ok"
        request = MagicMock()
        response = health_check(request)
        assert response.status_code == 503

    @patch("apps.core.health.cache")
    @patch("apps.core.health.connection")
    def test_cache_down(self, mock_conn, mock_cache):
        """Cache KO → 503."""
        mock_cache.set.side_effect = Exception("Redis down")
        request = MagicMock()
        response = health_check(request)
        assert response.status_code == 503

    @patch("apps.core.health.cache")
    @patch("apps.core.health.connection")
    def test_cache_mismatch(self, mock_conn, mock_cache):
        """Cache retourne mauvaise valeur → 503."""
        mock_cache.get.return_value = "wrong"
        request = MagicMock()
        response = health_check(request)
        assert response.status_code == 503
