"""
Tests complets pour l'application authentication.

Couvre : inscription, connexion, déconnexion, réinitialisation de mot de passe,
rafraîchissement de token, bonus quotidien.
"""

import datetime
from base64 import urlsafe_b64encode
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


# ── Inscription ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestRegister:
    """Tests d'inscription utilisateur."""

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("auth-register")

    def test_register_success(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
            "accept_privacy_policy": True,
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert "tokens" in response.data
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]
        assert "user" in response.data
        assert response.data["user"]["username"] == "newuser"

    def test_register_creates_user_in_db(self):
        data = {
            "username": "dbuser",
            "email": "dbuser@example.com",
            "password": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
            "accept_privacy_policy": True,
        }
        self.client.post(self.url, data)
        assert User.objects.filter(username="dbuser").exists()

    def test_register_privacy_policy_recorded(self):
        data = {
            "username": "privacyuser",
            "email": "privacy@example.com",
            "password": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
            "accept_privacy_policy": True,
        }
        self.client.post(self.url, data)
        user = User.objects.get(username="privacyuser")
        assert user.privacy_policy_accepted_at is not None

    def test_register_password_mismatch(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Str0ngP@ss!",
            "password2": "DifferentPass1!",
            "accept_privacy_policy": True,
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="dup@example.com",
            password="Str0ngP@ss!",
        )
        data = {
            "username": "newuser",
            "email": "dup@example.com",
            "password": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
            "accept_privacy_policy": True,
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_duplicate_username(self):
        User.objects.create_user(
            username="taken",
            email="taken@example.com",
            password="Str0ngP@ss!",
        )
        data = {
            "username": "taken",
            "email": "new@example.com",
            "password": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
            "accept_privacy_policy": True,
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_weak_password(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "123",
            "password2": "123",
            "accept_privacy_policy": True,
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_without_privacy_policy(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "Str0ngP@ss!",
            "password2": "Str0ngP@ss!",
            "accept_privacy_policy": False,
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_missing_fields(self):
        response = self.client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Connexion ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestLogin:
    """Tests de connexion utilisateur."""

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("auth-login")
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="Str0ngP@ss!",
        )

    def test_login_success(self):
        data = {"username": "loginuser", "password": "Str0ngP@ss!"}
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        assert "tokens" in response.data
        assert "access" in response.data["tokens"]
        assert "refresh" in response.data["tokens"]
        assert "user" in response.data

    def test_login_wrong_password(self):
        data = {"username": "loginuser", "password": "WrongPass!"}
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self):
        data = {"username": "ghost", "password": "Str0ngP@ss!"}
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_fields(self):
        response = self.client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_daily_bonus(self):
        """Première connexion du jour donne +2 pièces."""
        initial_coins = self.user.coins_balance
        data = {"username": "loginuser", "password": "Str0ngP@ss!"}
        self.client.post(self.url, data)
        self.user.refresh_from_db()
        assert self.user.coins_balance == initial_coins + 2
        assert self.user.last_daily_login == datetime.date.today()

    def test_login_daily_bonus_once_per_day(self):
        """Le bonus quotidien ne s'applique qu'une seule fois par jour."""
        self.user.last_daily_login = datetime.date.today()
        self.user.coins_balance = 10
        self.user.save()
        data = {"username": "loginuser", "password": "Str0ngP@ss!"}
        self.client.post(self.url, data)
        self.user.refresh_from_db()
        assert self.user.coins_balance == 10


# ── Déconnexion ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestLogout:
    """Tests de déconnexion (blacklist du refresh token)."""

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("auth-logout")
        self.user = User.objects.create_user(
            username="logoutuser",
            email="logout@example.com",
            password="Str0ngP@ss!",
        )

    def test_logout_blacklists_token(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(self.url, {"refresh": str(refresh)})
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_invalid_token(self):
        response = self.client.post(self.url, {"refresh": "invalidtoken"})
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_logout_no_token(self):
        response = self.client.post(self.url, {})
        assert response.status_code == status.HTTP_204_NO_CONTENT


# ── Rafraîchissement de token ────────────────────────────────────────────────


@pytest.mark.django_db
class TestTokenRefresh:
    """Tests du rafraîchissement de token JWT."""

    def setup_method(self):
        self.client = APIClient()
        self.url = reverse("token-refresh")
        self.user = User.objects.create_user(
            username="refreshuser",
            email="refresh@example.com",
            password="Str0ngP@ss!",
        )

    def test_token_refresh_success(self):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(self.user)
        response = self.client.post(self.url, {"refresh": str(refresh)})
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_token_refresh_invalid(self):
        response = self.client.post(self.url, {"refresh": "badtoken"})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── Réinitialisation de mot de passe ─────────────────────────────────────────


@pytest.mark.django_db
class TestPasswordReset:
    """Tests de la réinitialisation de mot de passe."""

    def setup_method(self):
        self.client = APIClient()
        self.request_url = reverse("password-reset-request")
        self.confirm_url = reverse("password-reset-confirm")
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="Str0ngP@ss!",
        )

    @patch("apps.authentication.views.send_mail")
    def test_password_reset_request_existing_email(self, mock_send_mail):
        response = self.client.post(self.request_url, {"email": "reset@example.com"})
        assert response.status_code == status.HTTP_200_OK
        assert mock_send_mail.called

    def test_password_reset_request_nonexistent_email(self):
        """Même réponse qu'un email existant (anti-énumération)."""
        response = self.client.post(self.request_url, {"email": "nobody@example.com"})
        assert response.status_code == status.HTTP_200_OK

    def test_password_reset_request_invalid_email(self):
        response = self.client.post(self.request_url, {"email": "notanemail"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_confirm_success(self):
        token_gen = PasswordResetTokenGenerator()
        token = token_gen.make_token(self.user)
        uid = urlsafe_b64encode(str(self.user.pk).encode()).decode()

        data = {
            "uid": uid,
            "token": token,
            "new_password": "NewStr0ng!Pass",
            "new_password2": "NewStr0ng!Pass",
        }
        response = self.client.post(self.confirm_url, data)
        assert response.status_code == status.HTTP_200_OK

        self.user.refresh_from_db()
        assert self.user.check_password("NewStr0ng!Pass")

    def test_password_reset_confirm_invalid_token(self):
        uid = urlsafe_b64encode(str(self.user.pk).encode()).decode()
        data = {
            "uid": uid,
            "token": "invalidtoken",
            "new_password": "NewStr0ng!Pass",
            "new_password2": "NewStr0ng!Pass",
        }
        response = self.client.post(self.confirm_url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_confirm_invalid_uid(self):
        data = {
            "uid": "baduid==",
            "token": "sometoken",
            "new_password": "NewStr0ng!Pass",
            "new_password2": "NewStr0ng!Pass",
        }
        response = self.client.post(self.confirm_url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_confirm_password_mismatch(self):
        token_gen = PasswordResetTokenGenerator()
        token = token_gen.make_token(self.user)
        uid = urlsafe_b64encode(str(self.user.pk).encode()).decode()

        data = {
            "uid": uid,
            "token": token,
            "new_password": "NewStr0ng!Pass",
            "new_password2": "Mismatch!Pass1",
        }
        response = self.client.post(self.confirm_url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
