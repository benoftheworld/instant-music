"""
URL configuration for authentication app.
"""

from django.urls import path

from .views import (
    ThrottledTokenRefreshView,
    login,
    logout,
    password_reset_confirm,
    password_reset_request,
    register,
)

urlpatterns = [
    path("register/", register, name="auth-register"),
    path("login/", login, name="auth-login"),
    path("logout/", logout, name="auth-logout"),
    path(
        "token/refresh/",
        ThrottledTokenRefreshView.as_view(),
        name="token-refresh",
    ),
    path(
        "password/reset/",
        password_reset_request,
        name="password-reset-request",
    ),
    path(
        "password/reset/confirm/",
        password_reset_confirm,
        name="password-reset-confirm",
    ),
]
