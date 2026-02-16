"""
Views for playlists app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Playlist, Track
from .serializers import (
    PlaylistSerializer, TrackSerializer,
    SpotifyPlaylistSerializer, SpotifyTrackSerializer
)
from .services import spotify_service, SpotifyAPIError
from .hybrid_service import hybrid_spotify_service


class PlaylistViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing cached playlists.
    """
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        parameters=[
            OpenApiParameter('query', str, description='Search query for playlists')
        ],
        responses={200: SpotifyPlaylistSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Search playlists on Spotify.
        
        Uses OAuth if user has connected Spotify, otherwise Client Credentials.
        
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
            # Use hybrid service with current user (OAuth if available)
            playlists = hybrid_spotify_service.search_playlists(
                query, 
                limit, 
                user=request.user if request.user.is_authenticated else None
            )
            
            # Add metadata about which mode is being used
            using_oauth = hybrid_spotify_service.is_using_oauth(request.user)
            
            serializer = SpotifyPlaylistSerializer(playlists, many=True)
            return Response({
                'playlists': serializer.data,
                'using_oauth': using_oauth,
                'mode': 'oauth' if using_oauth else 'client_credentials'
            })
        
        except SpotifyAPIError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    @extend_schema(
        responses={200: SpotifyPlaylistSerializer}
    )
    @action(detail=False, methods=['get'], url_path='spotify/(?P<spotify_id>[^/.]+)')
    def get_spotify_playlist(self, request, spotify_id=None):
        """
        Get playlist details from Spotify by ID.
        
        Uses OAuth if user has connected Spotify, otherwise Client Credentials.
        """
        try:
            # Use hybrid service with current user
            playlist = hybrid_spotify_service.get_playlist(
                spotify_id,
                user=request.user if request.user.is_authenticated else None
            )
            
            if not playlist:
                return Response(
                    {'error': 'Playlist not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = SpotifyPlaylistSerializer(playlist)
            return Response(serializer.data)
        
        except SpotifyAPIError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
    
    @extend_schema(
        responses={200: SpotifyTrackSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='spotify/(?P<spotify_id>[^/.]+)/tracks')
    def get_playlist_tracks(self, request, spotify_id=None):
        """
        Get tracks from a Spotify playlist.
        """
        try:
            limit = int(request.query_params.get('limit', 50))
        except ValueError:
            limit = 50
        
        try:
            tracks = spotify_service.get_playlist_tracks(spotify_id, limit)
            serializer = SpotifyTrackSerializer(tracks, many=True)
            return Response(serializer.data)
        
        except SpotifyAPIError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )


class TrackViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing cached tracks.
    """
    queryset = Track.objects.all()
    serializer_class = TrackSerializer
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={200: SpotifyTrackSerializer}
    )
    @action(detail=False, methods=['get'], url_path='spotify/(?P<spotify_id>[^/.]+)')
    def get_spotify_track(self, request, spotify_id=None):
        """
        Get track details from Spotify by ID.
        """
        try:
            track = spotify_service.get_track(spotify_id)
            
            if not track:
                return Response(
                    {'error': 'Track not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = SpotifyTrackSerializer(track)
            return Response(serializer.data)
        
        except SpotifyAPIError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

