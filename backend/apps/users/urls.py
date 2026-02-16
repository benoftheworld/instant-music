"""
URL configuration for users app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, FriendshipViewSet, TeamViewSet

router = DefaultRouter()
router.register(r'', UserViewSet, basename='user')

# Friendship routes
friendship_router = DefaultRouter()
friendship_router.register(r'', FriendshipViewSet, basename='friendship')

# Team routes
team_router = DefaultRouter()
team_router.register(r'', TeamViewSet, basename='team')

urlpatterns = [
    # These paths must come BEFORE the user router to avoid conflicts
    path('friends/', include(friendship_router.urls)),
    path('teams/', include(team_router.urls)),
    path('', include(router.urls)),
]
