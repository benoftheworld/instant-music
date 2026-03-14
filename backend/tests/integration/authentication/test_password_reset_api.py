"""Tests d'intégration de l'API password reset."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestPasswordResetRequest(BaseAPIIntegrationTest):
    """Vérifie la demande de réinitialisation de mot de passe."""

    def get_base_url(self):
        return "/api/auth/password/reset/"

    def test_reset_request_existing_email(self):
        user = UserFactory()
        client = self.get_client()
        resp = client.post(self.get_base_url(), {"email": user.email}, format="json")
        self.assert_status(resp, 200)

    def test_reset_request_nonexistent_email(self):
        # Always returns 200 to prevent email enumeration
        client = self.get_client()
        resp = client.post(
            self.get_base_url(), {"email": "nobody@example.com"}, format="json"
        )
        self.assert_status(resp, 200)

    def test_reset_request_missing_email(self):
        client = self.get_client()
        resp = client.post(self.get_base_url(), {}, format="json")
        self.assert_status(resp, 400)
