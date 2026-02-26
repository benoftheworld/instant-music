"""
URL configuration for games app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GameViewSet, KaraokeSongViewSet

router = DefaultRouter()
router.register(r'karaoke-songs', KaraokeSongViewSet, basename='karaoke-song')
router.register(r'', GameViewSet, basename='game')

urlpatterns = [
    path('', include(router.urls)),
]
