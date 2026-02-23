"""
URL configuration for apps/administration.
"""

from django.urls import path
from . import views

app_name = "administration"

urlpatterns = [
    path("status/", views.site_status, name="site-status"),
]
