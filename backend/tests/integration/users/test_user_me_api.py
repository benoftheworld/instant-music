"""Tests d'intégration de l'API utilisateurs."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestUserMeEndpoint(BaseAPIIntegrationTest):
    """Vérifie l'endpoint /api/users/me/."""

    def get_base_url(self):
        return "/api/users/me/"

    def test_get_me_authenticated(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert resp.data["username"] == user.username

    def test_get_me_unauthenticated(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 401)

    def test_patch_me(self):
        """PATCH /api/users/me/ — seul le champ avatar est modifiable."""
        user = UserFactory()
        client = self.get_auth_client(user)
        # Envoyer un PATCH vide (partial=True) doit réussir
        resp = client.patch(self.get_base_url(), {}, format="json")
        self.assert_status(resp, 200)
        assert resp.data["username"] == user.username
