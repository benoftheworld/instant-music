"""
Views for playlists app (Deezer + YouTube search helpers).
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .serializers import PlaylistSerializer
from .deezer_service import deezer_service, DeezerAPIError
from .youtube_service import youtube_service, YouTubeAPIError


class PlaylistViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    # Actions Deezer accessibles sans authentification (previews publics)
    PUBLIC_ACTIONS = {
        "search",
        "get_playlist",
        "get_playlist_tracks",
        "validate_playlist_access",
    }

    def get_permissions(self):
        if self.action in self.PUBLIC_ACTIONS:
            return [AllowAny()]
        return [IsAuthenticated()]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "query", str, description="Search query for playlists"
            )
        ],
        responses={200: PlaylistSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def search(self, request):
        query = request.query_params.get("query", "")
        if not query:
            return Response(
                {"error": "Query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            limit = int(request.query_params.get("limit", 20))
        except ValueError:
            limit = 20

        try:
            playlists = deezer_service.search_playlists(query, limit)
            serializer = PlaylistSerializer(playlists, many=True)
            return Response({"playlists": serializer.data, "source": "deezer"})
        except DeezerAPIError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @extend_schema(responses={200: PlaylistSerializer})
    @action(detail=False, methods=["get"], url_path="(?P<playlist_id>\d+)")
    def get_playlist(self, request, playlist_id=None):
        try:
            playlist = deezer_service.get_playlist(playlist_id)
            if not playlist:
                return Response(
                    {"error": "Playlist not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = PlaylistSerializer(playlist)
            return Response(serializer.data)
        except DeezerAPIError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(
        detail=False, methods=["get"], url_path="(?P<playlist_id>\d+)/tracks"
    )
    def get_playlist_tracks(self, request, playlist_id=None):
        try:
            limit = int(request.query_params.get("limit", 50))
        except ValueError:
            limit = 50
        try:
            tracks = deezer_service.get_playlist_tracks(playlist_id, limit)
            return Response(tracks)
        except DeezerAPIError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(
        detail=False, methods=["get"], url_path="(?P<playlist_id>\d+)/validate"
    )
    def validate_playlist_access(self, request, playlist_id=None):
        try:
            tracks = deezer_service.get_playlist_tracks(playlist_id, limit=5)
            return Response(
                {
                    "accessible": True,
                    "track_count": len(tracks),
                    "source": "deezer",
                }
            )
        except Exception as e:
            return Response(
                {"accessible": False, "error": str(e), "source": "deezer"},
                status=status.HTTP_200_OK,
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "query", str, description="Search query for YouTube songs"
            )
        ]
    )
    @action(detail=False, methods=["get"], url_path="youtube-songs/search")
    def search_youtube_songs(self, request):
        """Search YouTube for music videos (used for karaoke mode)."""
        query = request.query_params.get("query", "")
        if not query or len(query.strip()) < 2:
            return Response(
                {"error": "Le paramètre query est requis (min 2 caractères)."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            limit = min(int(request.query_params.get("limit", 10)), 20)
        except ValueError:
            limit = 10
        try:
            tracks = youtube_service.search_music_videos(
                query.strip(), limit=limit
            )
            return Response({"tracks": tracks, "source": "youtube"})
        except YouTubeAPIError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
