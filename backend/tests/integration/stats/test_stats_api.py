"""Tests d'intégration de l'API Stats."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestUserDetailedStats(BaseAPIIntegrationTest):
    """Vérifie les stats détaillées de l'utilisateur."""

    def get_base_url(self):
        return "/api/stats/me/"

    def test_get_my_stats(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert "total_games_played" in resp.data

    def test_stats_unauthenticated(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 401)


class TestLeaderboard(BaseAPIIntegrationTest):
    """Vérifie le classement général."""

    def get_base_url(self):
        return "/api/stats/leaderboard/"

    def test_get_leaderboard(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert "results" in resp.data


class TestTeamLeaderboard(BaseAPIIntegrationTest):
    """Vérifie le classement des équipes."""

    def get_base_url(self):
        return "/api/stats/leaderboard/teams/"

    def test_get_team_leaderboard(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)


class TestMyRank(BaseAPIIntegrationTest):
    """Vérifie le rang de l'utilisateur."""

    def get_base_url(self):
        return "/api/stats/my-rank/"

    def test_get_my_rank(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert "general_rank" in resp.data

    def test_rank_unauthenticated(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 401)


class TestUserPublicStats(BaseAPIIntegrationTest):
    """Vérifie les stats publiques d'un utilisateur."""

    def get_base_url(self):
        return "/api/stats/user/"

    def test_get_user_stats(self):
        target = UserFactory()
        viewer = UserFactory()
        client = self.get_auth_client(viewer)
        resp = client.get(f"{self.get_base_url()}{target.id}/")  # type: ignore[attr-defined]
        self.assert_status(resp, 200)
        assert resp.data["username"] == target.username

    def test_user_not_found(self):
        import uuid

        viewer = UserFactory()
        client = self.get_auth_client(viewer)
        resp = client.get(f"{self.get_base_url()}{uuid.uuid4()}/")
        self.assert_status(resp, 404)
