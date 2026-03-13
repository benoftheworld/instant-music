"""Utilitaires pour gérer le refresh token JWT via HttpOnly cookie.

Le refresh token n'est plus renvoyé dans le corps JSON de la réponse.
Il transite uniquement via un cookie HttpOnly + Secure + SameSite=Strict,
inaccessible au JavaScript client.
"""

from typing import cast

from django.conf import settings


# Nom du cookie — configurable via settings, fallback par défaut.
REFRESH_COOKIE_NAME = getattr(settings, "JWT_REFRESH_COOKIE_NAME", "refresh_token")


def set_refresh_cookie(response, refresh_token: str) -> None:
    """Attache le refresh token en cookie HttpOnly sur la réponse."""
    from datetime import timedelta

    max_age = settings.SIMPLE_JWT.get(
        "REFRESH_TOKEN_LIFETIME", timedelta(days=7)
    )
    if isinstance(max_age, timedelta):
        max_age = int(max_age.total_seconds())

    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=max_age,
        httponly=True,
        secure=getattr(settings, "JWT_REFRESH_COOKIE_SECURE", not settings.DEBUG),
        samesite=getattr(settings, "JWT_REFRESH_COOKIE_SAMESITE", "Strict"),
        path="/api/auth/",  # Restreint aux endpoints d'auth uniquement
    )


def clear_refresh_cookie(response) -> None:
    """Supprime le cookie refresh_token."""
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/auth/",
        samesite=getattr(settings, "JWT_REFRESH_COOKIE_SAMESITE", "Strict"),
    )


def get_refresh_from_cookie(request) -> str | None:
    """Extrait le refresh token depuis le cookie de la requête."""
    return cast("str | None", request.COOKIES.get(REFRESH_COOKIE_NAME))
