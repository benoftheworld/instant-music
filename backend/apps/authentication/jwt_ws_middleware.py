"""
Middleware ASGI pour valider un token JWT sur les connexions WebSocket.

Le token est extrait depuis le query param ?token=<jwt>.
Si invalide ou absent, la connexion est refusée avec le code 4003 (policy violation).
"""

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

logger = logging.getLogger("apps.authentication")

User = get_user_model()


class JwtWebSocketMiddleware(BaseMiddleware):
    """Injecte scope['user'] depuis un JWT en query param, ou ferme avec 4003."""

    async def __call__(self, scope, receive, send):
        if scope["type"] != "websocket":
            return await super().__call__(scope, receive, send)

        token_str = self._extract_token(scope)

        if not token_str:
            logger.warning(
                "ws_auth_rejected",
                extra={"reason": "token_absent", "path": scope.get("path")},
            )
            await send({"type": "websocket.close", "code": 4003})
            return

        try:
            token = AccessToken(token_str)
            user = await self._get_user(token["user_id"])
            if user is None:
                raise TokenError("user_not_found")
            scope["user"] = user
        except (InvalidToken, TokenError, Exception) as exc:
            logger.warning(
                "ws_auth_rejected",
                extra={
                    "reason": str(exc),
                    "path": scope.get("path"),
                },
            )
            await send({"type": "websocket.close", "code": 4003})
            return

        return await super().__call__(scope, receive, send)

    @staticmethod
    def _extract_token(scope) -> str | None:
        qs = parse_qs(scope.get("query_string", b"").decode())
        tokens = qs.get("token")
        return tokens[0] if tokens else None

    @staticmethod
    @database_sync_to_async
    def _get_user(user_id: str):
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            return None
