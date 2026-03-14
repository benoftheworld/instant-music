"""Tests d'intégration étendus — couverture des branches manquantes stats/views.py."""

import pytest
from rest_framework import status

from tests.base import BaseAPIIntegrationTest
from tests.factories import (
    GameAnswerFactory,
    GameFactory,
    GamePlayerFactory,
    GameRoundFactory,
    UserFactory,
)


@pytest.mark.django_db
class TestLeaderboardWithData(BaseAPIIntegrationTest):
    """Lines 147-155 — leaderboard loop body with actual game data."""

    def get_base_url(self):
        return "/api/stats/leaderboard/"

    def test_leaderboard_with_game_data(self, api_client):
        u1 = UserFactory()
        u2 = UserFactory()
        game = GameFactory(host=u1, status="finished")
        gp1 = GamePlayerFactory(game=game, user=u1, score=200, rank=1)
        gp2 = GamePlayerFactory(game=game, user=u2, score=100, rank=2)
        # Update user stats
        u1.total_points = 200
        u1.total_games_played = 1
        u1.total_wins = 1
        u1.save()
        u2.total_points = 100
        u2.total_games_played = 1
        u2.total_wins = 0
        u2.save()
        resp = api_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        results = resp.data.get("results", resp.data)
        # At least one entry with data
        assert len(results) >= 1


@pytest.mark.django_db
class TestLeaderboardByModeWithData(BaseAPIIntegrationTest):
    """Lines 147-155 — specific mode leaderboard."""

    def get_base_url(self):
        return "/api/stats/leaderboard/"

    def test_leaderboard_mode_classic(self, api_client):
        u1 = UserFactory()
        game = GameFactory(host=u1, status="finished", mode="classic")
        gp = GamePlayerFactory(game=game, user=u1, score=300, rank=1)
        u1.total_points = 300
        u1.total_games_played = 1
        u1.save()
        resp = api_client.get(f"{self.get_base_url()}classic/")
        self.assert_status(resp, status.HTTP_200_OK)


@pytest.mark.django_db
class TestTeamLeaderboardWithData(BaseAPIIntegrationTest):
    """Lines 195-202 — team leaderboard loop body."""

    def get_base_url(self):
        return "/api/stats/leaderboard/teams/"

    def test_team_leaderboard_with_data(self, api_client):
        from apps.users.models import Team, TeamMember
        owner = UserFactory()
        team = Team.objects.create(
            name="TestTeam", owner=owner, total_points=500, total_games=5, total_wins=3
        )
        TeamMember.objects.create(team=team, user=owner, role="owner")
        resp = api_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        results = resp.data.get("results", resp.data)
        assert len(results) >= 1
        entry = results[0]
        assert entry["name"] == "TestTeam"
        assert entry["total_points"] == 500
        assert "win_rate" in entry


@pytest.mark.django_db
class TestMyRankWithData(BaseAPIIntegrationTest):
    """Lines 259-261, 331 — my rank with per-mode rankings."""

    def get_base_url(self):
        return "/api/stats/my-rank/"

    def test_my_rank_with_game_data(self, auth_client, user):
        game = GameFactory(host=user, status="finished", mode="classic")
        gp = GamePlayerFactory(game=game, user=user, score=500, rank=1)
        user.total_points = 500
        user.total_games_played = 1
        user.save()
        resp = auth_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)
        assert "general_rank" in resp.data
        assert "mode_ranks" in resp.data
        assert resp.data["general_rank"] >= 1
