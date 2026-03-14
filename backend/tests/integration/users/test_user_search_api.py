"""Tests d'intégration de l'API de recherche d'utilisateurs."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestUserSearch(BaseAPIIntegrationTest):
    """Vérifie la recherche d'utilisateurs par username."""

    def get_base_url(self):
        return "/api/users/search/"

    def test_search_finds_user(self):
        user = UserFactory(username="searcher")
        UserFactory(username="findme")
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url(), {"q": "findme"})
        self.assert_status(resp, 200)
        assert any(u["username"] == "findme" for u in resp.data)

    def test_search_excludes_self(self):
        user = UserFactory(username="myself")
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url(), {"q": "myself"})
        self.assert_status(resp, 200)
        assert not any(u["username"] == "myself" for u in resp.data)

    def test_search_too_short_query(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url(), {"q": "a"})
        self.assert_status(resp, 200)
        assert resp.data == []

    def test_search_unauthenticated(self):
        client = self.get_client()
        resp = client.get(self.get_base_url(), {"q": "test"})
        self.assert_status(resp, 401)
