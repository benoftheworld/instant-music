"""
URL Configuration for playlists app (YouTube-backed).
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlaylistViewSet, TrackViewSet

router = DefaultRouter()
router.register(r'playlists', PlaylistViewSet, basename='playlist')
router.register(r'tracks', TrackViewSet, basename='track')

urlpatterns = [
    path('', include(router.urls)),
]
