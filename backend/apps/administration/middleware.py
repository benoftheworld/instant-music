"""
Maintenance middleware — blocks all non-admin/non-health requests when
maintenance mode is enabled in SiteConfiguration.

Excluded paths (always pass through):
  - /admin/      — Django admin
  - /api/health/ — Health check probes
  - /api/ready/  — Readiness probe
  - /api/alive/  — Liveness probe
  - /api/administration/status/ — so the frontend can fetch the maintenance message

Staff bypass:
  Authenticated users with is_staff=True bypass maintenance mode entirely.
  AuthenticationMiddleware must run before this middleware (guaranteed by
  the MIDDLEWARE order in settings).
"""

import json
import logging

from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# Paths that bypass maintenance mode entirely
_EXCLUDED_PREFIXES = (
    "/admin/",
    "/api/health/",
    "/api/ready/",
    "/api/alive/",
    "/api/administration/status/",
    "/static/",
    "/media/",
)


class MaintenanceMiddleware(MiddlewareMixin):
    """
    Returns HTTP 503 with a JSON body when maintenance_mode is True,
    except for whitelisted paths.

    The configuration is read from the DB on every request but cached in
    memory for 5 seconds via a simple class-level cache to avoid a DB hit
    on each incoming request.
    """

    _cached_maintenance: bool = False
    _cached_title: str = ""
    _cached_message: str = ""
    _cache_ts: float = 0.0
    _CACHE_TTL: float = 5.0  # seconds

    def _refresh_cache(self) -> None:
        """Reload SiteConfiguration from DB and update in-memory cache."""
        import time

        now = time.monotonic()
        if now - self._cache_ts < self._CACHE_TTL:
            return
        try:
            from apps.administration.models import SiteConfiguration

            cfg = SiteConfiguration.get_solo()
            MaintenanceMiddleware._cached_maintenance = cfg.maintenance_mode
            MaintenanceMiddleware._cached_title = cfg.maintenance_title
            MaintenanceMiddleware._cached_message = cfg.maintenance_message
        except Exception as exc:  # noqa: BLE001
            # If the table doesn't exist yet (migrations pending) — skip
            logger.debug("MaintenanceMiddleware: cannot read config: %s", exc)
            MaintenanceMiddleware._cached_maintenance = False
        MaintenanceMiddleware._cache_ts = now

    def process_request(self, request):
        self._refresh_cache()

        if not self._cached_maintenance:
            return None  # Let the request through

        path = request.path
        for prefix in _EXCLUDED_PREFIXES:
            if path.startswith(prefix):
                return None  # Whitelisted path — let through

        # Staff users bypass maintenance mode entirely.
        # AuthenticationMiddleware runs before MaintenanceMiddleware so
        # request.user is already populated here.
        user = getattr(request, "user", None)
        if user is not None and user.is_authenticated and user.is_staff:
            return None

        payload = {
            "maintenance": True,
            "title": self._cached_title or "Maintenance en cours",
            "message": self._cached_message or "Site temporairement indisponible.",
        }
        return HttpResponse(
            json.dumps(payload, ensure_ascii=False),
            status=503,
            content_type="application/json; charset=utf-8",
        )
