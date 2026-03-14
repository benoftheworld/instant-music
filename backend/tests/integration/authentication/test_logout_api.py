"""Tests d'intégration de l'API logout."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestAuthLogout(BaseAPIIntegrationTest):
    """Vérifie la déconnexion."""

    def get_base_url(self):
        return "/api/auth/logout/"

    def test_logout_success(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.post(self.get_base_url())
        self.assert_status(resp, 204)

    def test_logout_unauthenticated(self):
        client = self.get_client()
        resp = client.post(self.get_base_url())
        # logout is AllowAny so it succeeds even without auth
        self.assert_status(resp, 204)
