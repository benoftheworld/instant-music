"""
URL configuration for stats app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.UserDetailedStatsView.as_view(), name='user-detailed-stats'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('leaderboard/teams/', views.TeamLeaderboardView.as_view(), name='team-leaderboard'),
    path('leaderboard/<str:mode>/', views.LeaderboardByModeView.as_view(), name='leaderboard-by-mode'),
    path('my-rank/', views.MyRankView.as_view(), name='my-rank'),
]
