"""Décorateurs pour les vues playlists."""

import functools
import logging

from rest_framework import status
from rest_framework.response import Response

from apps.core.prometheus_metrics import EXTERNAL_API_REQUESTS_TOTAL

from .deezer_service import DeezerAPIError

logger = logging.getLogger("apps.playlists.views")


def handle_deezer_call(endpoint: str):
    """Décorateur pour les actions appelant l'API Deezer.

    Gère les métriques Prometheus et la gestion d'erreur de manière uniforme.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            EXTERNAL_API_REQUESTS_TOTAL.labels(
                service="deezer", endpoint=endpoint
            ).inc()
            try:
                return func(*args, **kwargs)
            except DeezerAPIError as e:
                logger.error(
                    f"deezer_{endpoint}_error",
                    extra={"endpoint": endpoint, "error": str(e)},
                )
                return Response(
                    {"error": str(e)},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        return wrapper

    return decorator
