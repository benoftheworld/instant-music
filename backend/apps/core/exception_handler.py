"""Handler d'exceptions DRF personnalisé.

Intercepte toutes les réponses d'erreur (4xx, 5xx) pour :
  - Logger le détail de l'erreur (body, user, path) en JSON structuré
  - Enrichir la réponse avec un request_id pour la traçabilité
  - Remonter les erreurs dans Kibana avec contexte exploitable
"""

import logging
import traceback

from rest_framework import status
from rest_framework.views import exception_handler

logger = logging.getLogger("apps.core.exceptions")


def custom_exception_handler(exc, context):
    """Gérer les exceptions DRF : log + enrichissement de chaque erreur API."""
    response = exception_handler(exc, context)

    request = context.get("request")
    view = context.get("view")
    view_name = (
        f"{view.__class__.__module__}.{view.__class__.__name__}"
        if view
        else "unknown"
    )

    user = getattr(request, "user", None) if request else None
    user_id = (
        user.id
        if user and hasattr(user, "is_authenticated") and user.is_authenticated
        else None
    )
    method = getattr(request, "method", None)
    path = getattr(request, "path", None)
    request_id = getattr(request, "_request_id", None)

    log_extra = {
        "request_id": request_id,
        "user_id": user_id,
        "method": method,
        "path": path,
        "view": view_name,
        "exception_type": type(exc).__name__,
    }

    if response is not None:
        # Erreurs gérées par DRF (ValidationError, PermissionDenied, NotFound…)
        status_code = response.status_code
        log_extra["status_code"] = status_code
        log_extra["error_detail"] = response.data

        if status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.error(
                "api_error_5xx",
                extra={**log_extra, "traceback": traceback.format_exc()},
            )
        elif status_code == status.HTTP_403_FORBIDDEN:
            logger.warning("api_forbidden", extra=log_extra)
        elif status_code == status.HTTP_401_UNAUTHORIZED:
            logger.warning("api_unauthorized", extra=log_extra)
        elif status_code == status.HTTP_404_NOT_FOUND:
            logger.info("api_not_found", extra=log_extra)
        elif status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            logger.warning("api_throttled", extra=log_extra)
        elif status_code >= status.HTTP_400_BAD_REQUEST:
            logger.warning("api_error_4xx", extra=log_extra)

    else:
        # Exception non gérée → 500 interne
        logger.error(
            "api_unhandled_exception",
            extra={
                **log_extra,
                "status_code": 500,
                "error_detail": str(exc),
                "traceback": traceback.format_exc(),
            },
        )

    return response
