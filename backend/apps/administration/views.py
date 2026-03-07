"""API views for administration (public-facing parts).

GET /api/administration/status/
  Returns maintenance status + active banner info.
  No authentication required — the frontend needs this even when logged out.
"""

from django.views.decorators.cache import never_cache
from rest_framework.decorators import api_view, authentication_classes, permission_classes
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
    """Return the content of a legal page (privacy policy or legal notices).
    No authentication required — accessible to all visitors.
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
