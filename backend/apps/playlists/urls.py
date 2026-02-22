"""
URL Configuration for playlists app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlaylistViewSet

router = DefaultRouter()
# Expose endpoints under /api/playlists/... (avoid duplicated 'playlists/playlists')
router.register(r'', PlaylistViewSet, basename='playlist')

urlpatterns = [
    path('', include(router.urls)),
]
