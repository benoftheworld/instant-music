"""Middleware de logging structuré pour les requêtes HTTP.

Enregistre chaque requête avec request_id, user_id, method, path,
status_code et duration_ms au format JSON.
Pour les erreurs 4xx/5xx, le body de la réponse est inclus dans les logs
afin de faciliter le diagnostic dans Kibana.
"""

import logging
import time
import uuid

logger = logging.getLogger("apps.core.http")


class StructuredLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = str(uuid.uuid4())
        request._request_id = request_id
        start = time.monotonic()

        response = self.get_response(request)

        duration_ms = round((time.monotonic() - start) * 1000, 1)
        user = getattr(request, "user", None)
        user_id = user.id if user and user.is_authenticated else None
        status_code = response.status_code

        extra = {
            "request_id": request_id,
            "user_id": user_id,
            "method": request.method,
            "path": request.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }

        # Inclure le body de la réponse d'erreur pour les 4xx et 5xx
        if status_code >= 400:
            response_body = self._get_response_body(response)
            if response_body:
                extra["response_body"] = response_body[:2000]

        if status_code >= 500:
            logger.error("http_request", extra=extra)
        elif status_code >= 400:
            logger.warning("http_request", extra=extra)
        else:
            logger.info("http_request", extra=extra)

        # Ajouter le request_id dans le header de réponse pour la traçabilité
        response["X-Request-ID"] = request_id
        return response

    @staticmethod
    def _get_response_body(response):
        """Extrait le body de la réponse de manière sûre."""
        try:
            content_type = response.get("Content-Type", "")
            if "application/json" in content_type:
                return response.content.decode("utf-8", errors="replace")
        except Exception:
            pass
        return None
