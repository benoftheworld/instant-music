"""API views for administration (public-facing parts).

GET /api/administration/status/
  Returns maintenance status + active banner info.
  No authentication required — the frontend needs this even when logged out.
"""

from django.views.decorators.cache import never_cache
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import LegalPage, SiteConfiguration


@never_cache
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def site_status(request):
    """Return current maintenance & banner state.

    Response shape:
    {
        "maintenance": false,
        "maintenance_title": "...",
        "maintenance_message": "...",
        "banner": {
            "enabled": true,
            "message": "...",
            "color": "info",
            "dismissible": true
        }
    }
    """
    cfg = SiteConfiguration.get_solo()
    return Response(
        {
            "maintenance": cfg.maintenance_mode,
            "maintenance_title": cfg.maintenance_title,
            "maintenance_message": cfg.maintenance_message,
            "banner": {
                "enabled": cfg.banner_enabled,
                "message": cfg.banner_message,
                "color": cfg.banner_color,
                "dismissible": cfg.banner_dismissible,
            },
        }
    )


@never_cache
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def legal_page(request, page_type: str):
    """Retourne le contenu d'une page légale.
    
    Args:
        request: HTTP request
        page_type: type de la page légale ("privacy", "terms", etc.)
    
    Response:
        200: {
            "page_type": "privacy",
            "title": "Politique de confidentialité",
            "content": "...",
            "updated_at": "2024-01-01T12:00:00Z"
        }
        404: {"detail": "Page introuvable."}

    """
    try:
        page = LegalPage.objects.get(page_type=page_type)
    except LegalPage.DoesNotExist:
        return Response({"detail": "Page introuvable."}, status=404)
    return Response(
        {
            "page_type": page.page_type,
            "title": page.title,
            "content": page.content,
            "updated_at": page.updated_at,
        }
    )
