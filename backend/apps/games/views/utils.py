"""Utility functions for game views."""

from __future__ import annotations

import random
import string

from rest_framework import status
from rest_framework.response import Response

from ..models import Game


def generate_room_code() -> str:
    """Generate a unique 6-character room code."""
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))  # nosec B311
        if not Game.objects.filter(room_code=code).exists():
            return code


def _maintenance_response_if_needed(user) -> Response | None:
    """Retourne une 503 si le site est en maintenance et que l'user n'est pas staff.

    Vérification de défense en profondeur : le MaintenanceMiddleware bloque déjà
    les non-staff au niveau HTTP, mais ce contrôle offre un message d'erreur
    spécifique aux opérations de jeu.
    """
    from apps.administration.models import SiteConfiguration

    try:
        cfg = SiteConfiguration.get_solo()
    except Exception:
        return None  # table absente (migrations en attente) — on laisse passer

    if not cfg.maintenance_mode:
        return None

    if user.is_staff:
        return None  # les staff peuvent toujours créer/rejoindre des parties

    return Response(
        {
            "error": (
                "Le site est en cours de maintenance."
                " Impossible de créer ou rejoindre une partie pour le moment."
            ),
            "maintenance": True,
            "maintenance_title": cfg.maintenance_title,
        },
        status=status.HTTP_503_SERVICE_UNAVAILABLE,
    )
