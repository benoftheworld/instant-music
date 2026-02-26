"""
URL configuration for InstantMusic project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.core.health import (
    health_check,
    readiness_check,
    liveness_check,
)
from apps.core.metrics import metrics as metrics_view

urlpatterns = [
    # Admin
    path("admin/", admin.site.urls),
    # Health checks
    path("api/health/", health_check, name="health"),
    path("api/ready/", readiness_check, name="readiness"),
    path("api/alive/", liveness_check, name="liveness"),
    # API Documentation
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
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
    # API endpoints
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
    # Prometheus metrics (scraped by Prometheus)
    path("metrics/", metrics_view),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
