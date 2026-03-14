"""Tests d'intégration supplémentaires du UserViewSet."""

import pytest
from rest_framework import status

from apps.users.models import User
from tests.base import BaseAPIIntegrationTest


@pytest.mark.django_db
class TestUserMe(BaseAPIIntegrationTest):
    """Vérifie les endpoints /me."""

    def get_base_url(self):
        return "/api/users/me/"

    def test_get_me(self, auth_client, user):
        resp = auth_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data["username"] == user.username

    def test_patch_me(self, auth_client, user):
        resp = auth_client.patch(
            self.get_base_url(),
            {"bio": "Updated bio"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)


@pytest.mark.django_db
class TestUserList(BaseAPIIntegrationTest):
    """Vérifie la liste d'utilisateurs."""

    def get_base_url(self):
        return "/api/users/"

    def test_list_as_regular_user(self, auth_client, user):
        resp = auth_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        # Regular user should only see themselves
        assert len(resp.data) >= 1

    def test_list_as_staff(self, staff_user, api_client):
        api_client.force_authenticate(user=staff_user)
        resp = api_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)


@pytest.mark.django_db
class TestUserChangePassword(BaseAPIIntegrationTest):
    """Vérifie le changement de mot de passe."""

    def get_base_url(self):
        return "/api/users/change_password/"

    def test_change_password_success(self, auth_client, user):
        resp = auth_client.post(
            self.get_base_url(),
            {
                "old_password": "Testpass123!",
                "new_password": "NewSecure@Pass1!",
                "new_password2": "NewSecure@Pass1!",
            },
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    def test_change_password_wrong_old(self, auth_client, user):
        resp = auth_client.post(
            self.get_base_url(),
            {
                "old_password": "WrongPass123!",
                "new_password": "NewSecure@Pass1!",
                "new_password2": "NewSecure@Pass1!",
            },
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestUserDeleteAccount(BaseAPIIntegrationTest):
    """Vérifie la suppression de compte."""

    def get_base_url(self):
        return "/api/users/delete_account/"

    def test_delete_account(self, auth_client, user):
        resp = auth_client.delete(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        assert not User.objects.filter(id=user.id).exists()


@pytest.mark.django_db
class TestUserSearch(BaseAPIIntegrationTest):
    """Vérifie la recherche d'utilisateurs."""

    def get_base_url(self):
        return "/api/users/search/"

    def test_search_too_short(self, auth_client):
        resp = auth_client.get(f"{self.get_base_url()}?q=a")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data == []

    def test_search_success(self, auth_client, user2):
        resp = auth_client.get(f"{self.get_base_url()}?q={user2.username[:3]}")
        self.assert_status(resp, status.HTTP_200_OK)


@pytest.mark.django_db
class TestUserExists(BaseAPIIntegrationTest):
    """Vérifie l'endpoint exists."""

    def get_base_url(self):
        return "/api/users/exists/"

    def test_exists_by_username(self, api_client, user):
        resp = api_client.get(f"{self.get_base_url()}?username={user.username}")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data["exists"] is True

    def test_exists_by_email(self, api_client, user):
        resp = api_client.get(f"{self.get_base_url()}?email={user.email}")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_exists_no_params(self, api_client):
        resp = api_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data["exists"] is False

    def test_exists_nonexistent_username(self, api_client):
        resp = api_client.get(f"{self.get_base_url()}?username=nonexistent_xyz")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data["exists"] is False


@pytest.mark.django_db
class TestUserExportData(BaseAPIIntegrationTest):
    """Vérifie l'export de données RGPD."""

    def get_base_url(self):
        return "/api/users/export_data/"

    def test_export_data(self, auth_client, user):
        resp = auth_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp["Content-Type"] == "application/json"
        assert "Content-Disposition" in resp


@pytest.mark.django_db
class TestUserCookieConsent(BaseAPIIntegrationTest):
    """Vérifie le consentement cookies."""

    def get_base_url(self):
        return "/api/users/cookie_consent/"

    def test_cookie_consent(self, auth_client, user):
        resp = auth_client.post(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        assert "consented_at" in resp.data

    def test_cookie_consent_idempotent(self, auth_client, user):
        auth_client.post(self.get_base_url())
        resp = auth_client.post(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
