"""Tests d'intégration de l'API de vérification d'existence."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestUserExists(BaseAPIIntegrationTest):
    """Vérifie l'endpoint /api/users/exists/."""

    def get_base_url(self):
        return "/api/users/exists/"

    def test_username_exists(self):
        UserFactory(username="alice")
        client = self.get_client()
        resp = client.get(self.get_base_url(), {"username": "alice"})
        self.assert_status(resp, 200)
        assert resp.data["exists"] is True

    def test_username_not_exists(self):
        client = self.get_client()
        resp = client.get(self.get_base_url(), {"username": "nobody"})
        self.assert_status(resp, 200)
        assert resp.data["exists"] is False

    def test_no_params(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert resp.data["exists"] is False
