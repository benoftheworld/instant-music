"""Tests d'intégration des vues d'authentification."""

import pytest
from rest_framework import status

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
        resp = api_client.post(
            f"{self.get_base_url()}register/", {}, format="json"
        )
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
        resp = api_client.post(
            f"{self.get_base_url()}login/", {}, format="json"
        )
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
        """Toujours 200 pour éviter l'énumération d'adresses."""
        resp = api_client.post(
            f"{self.get_base_url()}password/reset/",
            {"email": "nonexistent@example.com"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_password_reset_request_missing_email(self, api_client):
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
