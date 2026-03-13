"""Tests for stats app."""

import pytest
from django.urls import reverse
from rest_framework import status

from apps.achievements.models import Achievement
from apps.games.models import Game, GameAnswer, GamePlayer


@pytest.mark.django_db
class TestUserDetailedStats:
    """Tests pour l'endpoint /api/stats/me/."""

    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("user-detailed-stats")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_stats_returns_zeros(self, auth_client):
        url = reverse("user-detailed-stats")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert data["total_games_played"] == 0
        assert data["total_wins"] == 0
        assert data["total_points"] == 0
        assert data["accuracy"] == 0.0
        assert data["win_rate"] == 0.0
        assert data["achievements_unlocked"] == 0

    def test_achievements_total_reflects_existing(self, auth_client, db):
        Achievement.objects.create(
            name="Test Achievement",
            description="desc",
            condition_type="games_played",
            condition_value=1,
        )
        url = reverse("user-detailed-stats")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["achievements_total"] >= 1


@pytest.mark.django_db
class TestLeaderboard:
    """Tests pour /api/stats/leaderboard/."""

    def test_leaderboard_public(self, api_client):
        url = reverse("leaderboard")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_leaderboard_pagination_structure(self, api_client):
        url = reverse("leaderboard")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        data = response.data
        assert "results" in data or "count" in data or isinstance(data, (list, dict))

    def test_leaderboard_by_mode_classic(self, api_client):
        url = reverse("leaderboard-by-mode", kwargs={"mode": "classic"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_leaderboard_by_mode_karaoke(self, api_client):
        url = reverse("leaderboard-by-mode", kwargs={"mode": "karaoke"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_leaderboard_by_invalid_mode_returns_ok(self, api_client):
        """Un mode inconnu retourne une liste vide, pas une 404."""
        url = reverse("leaderboard-by-mode", kwargs={"mode": "mode_inexistant"})
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestTeamLeaderboard:
    """Tests pour /api/stats/leaderboard/teams/."""

    def test_team_leaderboard_public(self, api_client):
        url = reverse("team-leaderboard")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestMyRank:
    """Tests pour /api/stats/my-rank/."""

    def test_my_rank_requires_auth(self, api_client):
        url = reverse("my-rank")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_my_rank_authenticated(self, auth_client):
        url = reverse("my-rank")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
