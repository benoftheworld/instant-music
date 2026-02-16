"""
URL configuration for playlists app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlaylistViewSet, TrackViewSet
from .views_oauth import (
    spotify_authorize,
    spotify_callback,
    spotify_status,
    spotify_disconnect,
    spotify_refresh
)

router = DefaultRouter()
router.register(r'playlists', PlaylistViewSet, basename='playlist')
router.register(r'tracks', TrackViewSet, basename='track')

urlpatterns = [
    path('', include(router.urls)),
    
    # Spotify OAuth endpoints
    path('spotify/authorize/', spotify_authorize, name='spotify-authorize'),
    path('spotify/callback/', spotify_callback, name='spotify-callback'),
    path('spotify/status/', spotify_status, name='spotify-status'),
    path('spotify/disconnect/', spotify_disconnect, name='spotify-disconnect'),
    path('spotify/refresh/', spotify_refresh, name='spotify-refresh'),
]
