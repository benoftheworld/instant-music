"""URL configuration for InstantMusic project."""

import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.core.health import (
    health_check,
    liveness_check,
    readiness_check,
)
from apps.core.metrics import metrics as metrics_view

# Path admin configurable via variable d'environnement (sécurité par obscurité).
# En production, définir ADMIN_URL à une valeur non prévisible.
# Ex : ADMIN_URL=manage-7f3a9c2b/
ADMIN_URL = os.environ.get("ADMIN_URL", "admin/")

urlpatterns = [
    # Admin
    path(ADMIN_URL, admin.site.urls),
    # Health checks
    path("api/health/", health_check, name="health"),
    path("api/ready/", readiness_check, name="readiness"),
    path("api/alive/", liveness_check, name="liveness"),
    # API Documentation (restricted to DEBUG mode or staff users in production)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
]

# API docs only available in DEBUG mode
if settings.DEBUG:
    urlpatterns += [
        path(
            "api/docs/",
            SpectacularSwaggerView.as_view(url_name="schema"),
            name="swagger-ui",
        ),
        path(
            "api/redoc/",
            SpectacularRedocView.as_view(url_name="schema"),
            name="redoc",
        ),
    ]

urlpatterns += [
    path("api/auth/", include("apps.authentication.urls")),
    path("api/users/", include("apps.users.urls")),
    path("api/games/", include("apps.games.urls")),
    path("api/achievements/", include("apps.achievements.urls")),
    path("api/playlists/", include("apps.playlists.urls")),
    # Backwards-compatible mount to support older frontend bundles that
    # request /api/playlists/playlists/... — keep until clients are rebuilt.
    path("api/playlists/playlists/", include("apps.playlists.urls")),
    path("api/stats/", include("apps.stats.urls")),
    path("api/administration/", include("apps.administration.urls")),
    path("api/shop/", include("apps.shop.urls")),
    # Prometheus metrics (scraped by Prometheus)
    path("metrics/", metrics_view),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
