"""Tests d'intégration des vues d'authentification."""

from base64 import urlsafe_b64encode
from unittest.mock import patch

import pytest
from django.contrib.auth.tokens import default_token_generator
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from tests.base import BaseAPIIntegrationTest


@pytest.mark.django_db
class TestAuthRegister(BaseAPIIntegrationTest):
    """Vérifie l'endpoint d'inscription."""

    def get_base_url(self):
        return "/api/auth/"

    def test_register_success(self, api_client):
        resp = api_client.post(
            f"{self.get_base_url()}register/",
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "Str0ngP@ss!1",
                "password2": "Str0ngP@ss!1",
                "accept_privacy_policy": True,
            },
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)
        assert "user" in resp.data
        assert "tokens" in resp.data

    def test_register_missing_fields(self, api_client):
        resp = api_client.post(f"{self.get_base_url()}register/", {}, format="json")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self, api_client):
        resp = api_client.post(
            f"{self.get_base_url()}register/",
            {
                "username": "newuser2",
                "email": "new2@example.com",
                "password": "Str0ngP@ss!1",
                "password2": "Different1!",
                "accept_privacy_policy": True,
            },
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self, api_client, user):
        resp = api_client.post(
            f"{self.get_base_url()}register/",
            {
                "username": user.username,
                "email": "other@example.com",
                "password": "Str0ngP@ss!1",
                "password2": "Str0ngP@ss!1",
                "accept_privacy_policy": True,
            },
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_register_username_too_long(self, api_client):
        """Un pseudonyme de plus de 20 caractères doit être rejeté."""
        resp = api_client.post(
            f"{self.get_base_url()}register/",
            {
                "username": "a" * 21,
                "email": "toolong_username@example.com",
                "password": "Str0ngP@ss!1",
                "password2": "Str0ngP@ss!1",
                "accept_privacy_policy": True,
            },
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)
        assert "username" in resp.data

    def test_register_username_exactly_20(self, api_client):
        """Un pseudonyme de exactement 20 caractères doit être accepté."""
        resp = api_client.post(
            f"{self.get_base_url()}register/",
            {
                "username": "a" * 20,
                "email": "exactly20@example.com",
                "password": "Str0ngP@ss!1",
                "password2": "Str0ngP@ss!1",
                "accept_privacy_policy": True,
            },
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)

    def test_register_email_too_long(self, api_client):
        """Un email de plus de 50 caractères doit être rejeté."""
        long_email = "a" * 40 + "@example.com"  # 52 chars
        resp = api_client.post(
            f"{self.get_base_url()}register/",
            {
                "username": "validuser",
                "email": long_email,
                "password": "Str0ngP@ss!1",
                "password2": "Str0ngP@ss!1",
                "accept_privacy_policy": True,
            },
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)
        assert "email" in resp.data

    def test_register_email_exactly_50(self, api_client):
        """Un email de exactement 50 caractères doit être accepté."""
        # Construct: prefix + "@" + domain so total = 50
        # "a" * 38 + "@example.com" = 38 + 12 = 50
        email_50 = "a" * 38 + "@example.com"
        assert len(email_50) == 50
        resp = api_client.post(
            f"{self.get_base_url()}register/",
            {
                "username": "validuser2",
                "email": email_50,
                "password": "Str0ngP@ss!1",
                "password2": "Str0ngP@ss!1",
                "accept_privacy_policy": True,
            },
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)


@pytest.mark.django_db
class TestAuthLogin(BaseAPIIntegrationTest):
    """Vérifie l'endpoint de connexion."""

    def get_base_url(self):
        return "/api/auth/"

    def test_login_success(self, api_client, user):
        resp = api_client.post(
            f"{self.get_base_url()}login/",
            {"username": user.username, "password": "Testpass123!"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)
        assert "user" in resp.data
        assert "tokens" in resp.data

    def test_login_wrong_password(self, api_client, user):
        resp = api_client.post(
            f"{self.get_base_url()}login/",
            {"username": user.username, "password": "wrongpass"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self, api_client):
        resp = api_client.post(
            f"{self.get_base_url()}login/",
            {"username": "nobody", "password": "anything"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_fields(self, api_client):
        resp = api_client.post(f"{self.get_base_url()}login/", {}, format="json")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestAuthLogout(BaseAPIIntegrationTest):
    """Vérifie l'endpoint de déconnexion."""

    def get_base_url(self):
        return "/api/auth/"

    def test_logout_without_cookie(self, api_client):
        resp = api_client.post(f"{self.get_base_url()}logout/")
        self.assert_status(resp, status.HTTP_204_NO_CONTENT)


@pytest.mark.django_db
class TestAuthPasswordReset(BaseAPIIntegrationTest):
    """Vérifie les endpoints de réinitialisation de mot de passe."""

    def get_base_url(self):
        return "/api/auth/"

    def test_password_reset_request_always_200(self, api_client):
        """Toujours 200 pour éviter l'énumération de pseudonymes."""
        resp = api_client.post(
            f"{self.get_base_url()}password/reset/",
            {"username": "nonexistentuser"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_password_reset_request_with_existing_username(self, api_client, user):
        """Toujours 200 même si le pseudonyme existe (anti-énumération)."""
        with patch("apps.authentication.views.send_mail"):
            resp = api_client.post(
                f"{self.get_base_url()}password/reset/",
                {"username": user.username},
                format="json",
            )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_password_reset_request_missing_username(self, api_client):
        """Le champ username est obligatoire."""
        resp = api_client.post(
            f"{self.get_base_url()}password/reset/",
            {},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_invalid_token(self, api_client):
        resp = api_client.post(
            f"{self.get_base_url()}password/reset/confirm/",
            {"uid": "baduid", "token": "badtoken", "new_password": "NewP@ss123!"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm_missing_fields(self, api_client):
        resp = api_client.post(
            f"{self.get_base_url()}password/reset/confirm/",
            {},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestTokenRefresh(BaseAPIIntegrationTest):
    """Vérifie le rafraîchissement du token."""

    def get_base_url(self):
        return "/api/auth/"

    def test_refresh_without_cookie(self, api_client):
        resp = api_client.post(f"{self.get_base_url()}token/refresh/")
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_with_valid_cookie(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        api_client.cookies["refresh_token"] = str(refresh)
        resp = api_client.post(f"{self.get_base_url()}token/refresh/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert "access" in resp.data


@pytest.mark.django_db
class TestAuthLoginDailyBonus(BaseAPIIntegrationTest):
    """Vérifie le bonus quotidien de connexion."""

    def get_base_url(self):
        return "/api/auth/"

    def test_login_awards_daily_bonus(self, api_client, user):
        initial_balance = user.coins_balance
        resp = api_client.post(
            f"{self.get_base_url()}login/",
            {"username": user.username, "password": "Testpass123!"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)
        user.refresh_from_db()
        assert user.coins_balance == initial_balance + 2
        assert user.last_daily_login is not None

    def test_login_no_double_daily_bonus(self, api_client, user):
        # First login
        api_client.post(
            f"{self.get_base_url()}login/",
            {"username": user.username, "password": "Testpass123!"},
            format="json",
        )
        user.refresh_from_db()
        balance_after_first = user.coins_balance
        # Second login same day
        api_client.post(
            f"{self.get_base_url()}login/",
            {"username": user.username, "password": "Testpass123!"},
            format="json",
        )
        user.refresh_from_db()
        assert user.coins_balance == balance_after_first

    def test_login_with_email(self, api_client, user):
        resp = api_client.post(
            f"{self.get_base_url()}login/",
            {"username": user.email, "password": "Testpass123!"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_login_with_nonexistent_email(self, api_client):
        """Lines 144-149 — email login with unknown email returns 401."""
        resp = api_client.post(
            f"{self.get_base_url()}login/",
            {"username": "unknown@example.com", "password": "whatever"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)


@pytest.mark.django_db
class TestAuthLogoutWithToken(BaseAPIIntegrationTest):
    """Vérifie la déconnexion avec un refresh token valide."""

    def get_base_url(self):
        return "/api/auth/"

    def test_logout_with_valid_cookie(self, api_client, user):
        refresh = RefreshToken.for_user(user)
        api_client.cookies["refresh_token"] = str(refresh)
        resp = api_client.post(f"{self.get_base_url()}logout/")
        self.assert_status(resp, status.HTTP_204_NO_CONTENT)


@pytest.mark.django_db
class TestPasswordResetFlow(BaseAPIIntegrationTest):
    """Vérifie le flux complet de réinitialisation du mot de passe."""

    def get_base_url(self):
        return "/api/auth/"

    @patch("apps.authentication.views.send_mail")
    def test_password_reset_request_existing_user(self, mock_mail, api_client, user):
        resp = api_client.post(
            f"{self.get_base_url()}password/reset/",
            {"username": user.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)
        mock_mail.assert_called_once()

    @patch("apps.authentication.views.send_mail", side_effect=Exception("SMTP fail"))
    def test_password_reset_send_mail_exception(self, mock_mail, api_client, user):
        """Lines 271-272 — send_mail fails but response is still 200."""
        resp = api_client.post(
            f"{self.get_base_url()}password/reset/",
            {"username": user.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_password_reset_confirm_valid_token(self, api_client, user):
        uid = urlsafe_b64encode(str(user.pk).encode()).decode()
        token = default_token_generator.make_token(user)
        resp = api_client.post(
            f"{self.get_base_url()}password/reset/confirm/",
            {
                "uid": uid,
                "token": token,
                "new_password": "NewSecure@Pass123!",
                "new_password2": "NewSecure@Pass123!",
            },
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)
        user.refresh_from_db()
        assert user.check_password("NewSecure@Pass123!")
