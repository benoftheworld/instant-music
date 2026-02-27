"""
URL configuration for authentication app.
"""

from django.urls import path
from .views import register, login, ThrottledTokenRefreshView

urlpatterns = [
    path("register/", register, name="auth-register"),
    path("login/", login, name="auth-login"),
    path(
        "token/refresh/",
        ThrottledTokenRefreshView.as_view(),
        name="token-refresh",
    ),
]
