"""Middleware Prometheus pour tracer les métriques HTTP.

Intercepte chaque requête pour mesurer :
- Le nombre total de requêtes par méthode/endpoint/code de réponse
- La durée de traitement de chaque requête
- Le nombre de requêtes en cours de traitement
"""

import re
import time

from apps.core.prometheus_metrics import (
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
    HTTP_REQUESTS_TOTAL,
)

# Patterns pour normaliser les URLs (éviter la cardinalité infinie)
URL_PATTERNS = [
    (re.compile(r"/api/games/[A-Z0-9]{6}/"), "/api/games/{room_code}/"),
    (re.compile(r"/api/users/\d+/"), "/api/users/{id}/"),
    (re.compile(r"/api/achievements/\d+/"), "/api/achievements/{id}/"),
    (re.compile(r"/api/playlists/\d+/"), "/api/playlists/{id}/"),
]

# Endpoints à exclure du tracking (health checks, métriques elles-mêmes)
EXCLUDED_PATHS = {"/metrics/", "/api/health/", "/api/ready/", "/api/alive/"}


def _normalize_path(path: str) -> str:
    """Normalise le chemin pour éviter l'explosion des labels."""
    for pattern, replacement in URL_PATTERNS:
        path = pattern.sub(replacement, path)
    return path


class PrometheusMetricsMiddleware:
    """Middleware Django pour collecter les métriques HTTP Prometheus."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Ne pas traquer les endpoints exclus
        if path in EXCLUDED_PATHS:
            return self.get_response(request)

        method = request.method
        endpoint = _normalize_path(path)

        HTTP_REQUESTS_IN_PROGRESS.labels(method=method).inc()
        start_time = time.monotonic()

        try:
            response = self.get_response(request)
            status_code = str(response.status_code)
        except Exception:
            status_code = "500"
            raise
        finally:
            duration = time.monotonic() - start_time
            HTTP_REQUESTS_IN_PROGRESS.labels(method=method).dec()
            HTTP_REQUESTS_TOTAL.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                endpoint=endpoint,
            ).observe(duration)

        return response
