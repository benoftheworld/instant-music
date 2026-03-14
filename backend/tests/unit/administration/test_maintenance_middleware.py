"""Tests unitaires du MaintenanceMiddleware."""

import json
import time
from unittest.mock import MagicMock, patch

from apps.administration.middleware import _EXCLUDED_PREFIXES, MaintenanceMiddleware
from tests.base import BaseUnitTest


class TestMaintenanceMiddleware(BaseUnitTest):
    """Vérifie le comportement du middleware de maintenance."""

    def get_target_class(self):
        return MaintenanceMiddleware

    def setup_method(self):
        self.middleware = MaintenanceMiddleware(get_response=lambda r: None)
        # Reset le cache entre chaque test
        MaintenanceMiddleware._cached_maintenance = False
        MaintenanceMiddleware._cached_title = ""
        MaintenanceMiddleware._cached_message = ""
        MaintenanceMiddleware._cache_ts = 0.0

    # ── Maintenance inactive ────────────────────────────────────────

    def test_maintenance_off_passes(self):
        """Sans maintenance, la requête passe."""
        MaintenanceMiddleware._cached_maintenance = False
        MaintenanceMiddleware._cache_ts = time.monotonic()
        request = MagicMock()
        request.path = "/api/games/"
        result = self.middleware.process_request(request)
        assert result is None

    # ── Maintenance active ──────────────────────────────────────────

    def test_maintenance_on_returns_503(self):
        MaintenanceMiddleware._cached_maintenance = True
        MaintenanceMiddleware._cached_title = "En travaux"
        MaintenanceMiddleware._cached_message = "Revenez plus tard"
        MaintenanceMiddleware._cache_ts = time.monotonic()

        request = MagicMock()
        request.path = "/api/games/"
        request.user = MagicMock()
        request.user.is_authenticated = False

        result = self.middleware.process_request(request)
        assert result is not None
        assert result.status_code == 503
        body = json.loads(result.content)
        assert body["maintenance"] is True
        assert body["title"] == "En travaux"
        assert body["message"] == "Revenez plus tard"

    # ── Exclusions ──────────────────────────────────────────────────

    def test_excluded_admin_passes(self):
        MaintenanceMiddleware._cached_maintenance = True
        MaintenanceMiddleware._cache_ts = time.monotonic()
        request = MagicMock()
        request.path = "/admin/login/"
        result = self.middleware.process_request(request)
        assert result is None

    def test_excluded_health_passes(self):
        MaintenanceMiddleware._cached_maintenance = True
        MaintenanceMiddleware._cache_ts = time.monotonic()
        request = MagicMock()
        request.path = "/api/health/"
        result = self.middleware.process_request(request)
        assert result is None

    def test_excluded_ready_passes(self):
        MaintenanceMiddleware._cached_maintenance = True
        MaintenanceMiddleware._cache_ts = time.monotonic()
        request = MagicMock()
        request.path = "/api/ready/"
        result = self.middleware.process_request(request)
        assert result is None

    def test_excluded_alive_passes(self):
        MaintenanceMiddleware._cached_maintenance = True
        MaintenanceMiddleware._cache_ts = time.monotonic()
        request = MagicMock()
        request.path = "/api/alive/"
        result = self.middleware.process_request(request)
        assert result is None

    def test_excluded_admin_status_passes(self):
        MaintenanceMiddleware._cached_maintenance = True
        MaintenanceMiddleware._cache_ts = time.monotonic()
        request = MagicMock()
        request.path = "/api/administration/status/"
        result = self.middleware.process_request(request)
        assert result is None

    def test_excluded_static_passes(self):
        MaintenanceMiddleware._cached_maintenance = True
        MaintenanceMiddleware._cache_ts = time.monotonic()
        request = MagicMock()
        request.path = "/static/css/main.css"
        result = self.middleware.process_request(request)
        assert result is None

    # ── Staff bypass ────────────────────────────────────────────────

    def test_staff_bypasses_maintenance(self):
        MaintenanceMiddleware._cached_maintenance = True
        MaintenanceMiddleware._cache_ts = time.monotonic()
        request = MagicMock()
        request.path = "/api/games/"
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.is_staff = True
        result = self.middleware.process_request(request)
        assert result is None

    def test_non_staff_auth_blocked(self):
        MaintenanceMiddleware._cached_maintenance = True
        MaintenanceMiddleware._cache_ts = time.monotonic()
        request = MagicMock()
        request.path = "/api/games/"
        request.user = MagicMock()
        request.user.is_authenticated = True
        request.user.is_staff = False
        result = self.middleware.process_request(request)
        assert result is not None
        assert result.status_code == 503

    # ── Cache TTL ───────────────────────────────────────────────────

    @patch("apps.administration.models.SiteConfiguration")
    def test_refresh_cache_on_ttl_expired(self, mock_site_config):
        """Après le TTL, le cache est rafraîchi depuis la DB."""
        MaintenanceMiddleware._cache_ts = 0.0  # Force expiration
        mock_cfg = MagicMock()
        mock_cfg.maintenance_mode = True
        mock_cfg.maintenance_title = "Titre"
        mock_cfg.maintenance_message = "Message"
        mock_site_config.get_solo.return_value = mock_cfg

        self.middleware._refresh_cache()

        assert MaintenanceMiddleware._cached_maintenance is True
        assert MaintenanceMiddleware._cached_title == "Titre"

    def test_no_refresh_within_ttl(self):
        """Le cache n'est pas rafraîchi pendant le TTL."""
        MaintenanceMiddleware._cached_maintenance = True
        MaintenanceMiddleware._cache_ts = time.monotonic()  # vient d'être mis à jour

        # Ne devrait pas appeler get_solo
        with patch("apps.administration.models.SiteConfiguration") as mock_config:
            self.middleware._refresh_cache()
            mock_config.get_solo.assert_not_called()

    # ── Constantes ──────────────────────────────────────────────────

    def test_excluded_prefixes(self):
        assert "/admin/" in _EXCLUDED_PREFIXES
        assert "/api/health/" in _EXCLUDED_PREFIXES
        assert "/api/ready/" in _EXCLUDED_PREFIXES
        assert "/api/alive/" in _EXCLUDED_PREFIXES
        assert "/api/administration/status/" in _EXCLUDED_PREFIXES

    def test_default_title_and_message(self):
        """503 avec titre/message vides utilise des valeurs par défaut."""
        MaintenanceMiddleware._cached_maintenance = True
        MaintenanceMiddleware._cached_title = ""
        MaintenanceMiddleware._cached_message = ""
        MaintenanceMiddleware._cache_ts = time.monotonic()

        request = MagicMock()
        request.path = "/api/test/"
        request.user = MagicMock()
        request.user.is_authenticated = False

        result = self.middleware.process_request(request)
        body = json.loads(result.content)
        assert body["title"] == "Maintenance en cours"
        assert body["message"] == "Site temporairement indisponible."
