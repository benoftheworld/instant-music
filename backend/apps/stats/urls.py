"""
URL configuration for stats app.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('me/', views.UserDetailedStatsView.as_view(), name='user-detailed-stats'),
]
