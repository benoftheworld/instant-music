"""Tests d'intégration de l'API password reset."""

from unittest.mock import patch

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestPasswordResetRequest(BaseAPIIntegrationTest):
    """Vérifie la demande de réinitialisation de mot de passe par pseudonyme."""

    def get_base_url(self):
        return "/api/auth/password/reset/"

    def test_reset_request_existing_username(self):
        user = UserFactory()
        client = self.get_client()
        with patch("apps.authentication.views.send_mail"):
            resp = client.post(self.get_base_url(), {"username": user.username}, format="json")
        self.assert_status(resp, 200)

    def test_reset_request_nonexistent_username(self):
        # Always returns 200 to prevent username enumeration
        client = self.get_client()
        resp = client.post(
            self.get_base_url(), {"username": "nobody_here"}, format="json"
        )
        self.assert_status(resp, 200)

    def test_reset_request_missing_username(self):
        client = self.get_client()
        resp = client.post(self.get_base_url(), {}, format="json")
        self.assert_status(resp, 400)
