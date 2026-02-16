"""
Views for playlists app (YouTube-backed).
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Playlist, Track
from .serializers import PlaylistSerializer, TrackSerializer, YouTubePlaylistSerializer
from .youtube_service import youtube_service, YouTubeAPIError


class PlaylistViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for playlists (YouTube-backed)."""
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        parameters=[
            OpenApiParameter('query', str, description='Search query for playlists')
        ],
        responses={200: YouTubePlaylistSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search playlists on YouTube.
        
        Query params:
        - query: Search string (required)
        - limit: Max results (optional, default: 20)
        """
        query = request.query_params.get('query', '')
        
        if not query:
            return Response(
                {'error': 'Query parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            limit = int(request.query_params.get('limit', 20))
        except ValueError:
            limit = 20
        
        try:
            playlists = youtube_service.search_playlists(query, limit)
            serializer = YouTubePlaylistSerializer(playlists, many=True)
            return Response({
                'playlists': serializer.data,
                'source': 'youtube'
            })
        except YouTubeAPIError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    @extend_schema(
        responses={200: YouTubePlaylistSerializer}
    )
    @action(detail=False, methods=['get'], url_path='youtube/(?P<youtube_id>[^/.]+)')
    def get_youtube_playlist(self, request, youtube_id=None):
        """Get playlist details from YouTube by ID."""
        try:
            playlist = youtube_service.get_playlist(youtube_id)
            
            if not playlist:
                return Response(
                    {'error': 'Playlist not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = YouTubePlaylistSerializer(playlist)
            return Response(serializer.data)
        except YouTubeAPIError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    @action(detail=False, methods=['get'], url_path='youtube/(?P<youtube_id>[^/.]+)/tracks')
    def get_playlist_tracks(self, request, youtube_id=None):
        """Get tracks/videos from a YouTube playlist."""
        try:
            limit = int(request.query_params.get('limit', 50))
        except ValueError:
            limit = 50
        
        try:
            tracks = youtube_service.get_playlist_tracks(youtube_id, limit)
            return Response(tracks)
        except YouTubeAPIError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    @action(detail=False, methods=['get'], url_path='youtube/(?P<youtube_id>[^/.]+)/validate')
    def validate_playlist_access(self, request, youtube_id=None):
        """Validate if a YouTube playlist is accessible."""
        try:
            tracks = youtube_service.get_playlist_tracks(youtube_id, limit=5)
            return Response({
                'accessible': True,
                'track_count': len(tracks),
                'source': 'youtube'
            })
        except Exception as e:
            return Response({
                'accessible': False,
                'error': str(e),
                'source': 'youtube'
            }, status=status.HTTP_200_OK)


class TrackViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for cached tracks."""
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = [IsAuthenticated]
