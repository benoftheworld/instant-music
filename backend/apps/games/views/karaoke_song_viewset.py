"""ViewSet for KaraokeSong catalogue."""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from ..models import KaraokeSong
from ..serializers import KaraokeSongSerializer


class KaraokeSongViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset exposing the KaraokeSong catalogue to authenticated players.

    Admins manage entries via Django admin.
    """

    serializer_class = KaraokeSongSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Return active karaoke songs ordered by artist and title."""
        return KaraokeSong.objects.filter(is_active=True).order_by("artist", "title")
