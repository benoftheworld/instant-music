"""Tests d'intégration de l'API Achievements."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import AchievementFactory, UserFactory


class TestAchievementList(BaseAPIIntegrationTest):
    """Vérifie la liste des achievements."""

    def get_base_url(self):
        return "/api/achievements/"

    def test_list_achievements(self):
        AchievementFactory()
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert len(resp.data) >= 1

    def test_list_unauthenticated(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 401)


class TestMyAchievements(BaseAPIIntegrationTest):
    """Vérifie les achievements débloqués par l'utilisateur."""

    def get_base_url(self):
        return "/api/achievements/mine/"

    def test_my_achievements_empty(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert resp.data["results"] == [] or resp.data == []

    def test_my_achievements_unauthenticated(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 401)
