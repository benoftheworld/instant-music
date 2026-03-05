"""Middleware de logging structuré pour les requêtes HTTP.

Enregistre chaque requête avec request_id, user_id, method, path,
status_code et duration_ms au format JSON.
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
        start = time.monotonic()

        response = self.get_response(request)

        duration_ms = round((time.monotonic() - start) * 1000, 1)
        user = getattr(request, "user", None)
        user_id = user.id if user and user.is_authenticated else None

        logger.info(
            "http_request",
            extra={
                "request_id": request_id,
                "user_id": user_id,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
