"""Tests for achievements app."""

import pytest
from django.urls import reverse
from rest_framework import status

from .models import Achievement, UserAchievement


@pytest.fixture()
def achievement(db):
    return Achievement.objects.create(
        name="Premier pas",
        description="Jouer sa première partie.",
        points=10,
        condition_type="games_played",
        condition_value=1,
    )


@pytest.mark.django_db
class TestAchievementList:
    """Tests pour GET /api/achievements/."""

    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("achievement-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_returns_list(self, auth_client, achievement):
        url = reverse("achievement-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert any(a["name"] == achievement.name for a in response.data)

    def test_unlocked_false_when_not_earned(self, auth_client, achievement):
        url = reverse("achievement-list")
        response = auth_client.get(url)
        entry = next(a for a in response.data if a["name"] == achievement.name)
        assert entry["unlocked"] is False

    def test_unlocked_true_after_grant(self, auth_client, user, achievement):
        UserAchievement.objects.create(user=user, achievement=achievement)
        url = reverse("achievement-list")
        response = auth_client.get(url)
        entry = next(a for a in response.data if a["name"] == achievement.name)
        assert entry["unlocked"] is True


@pytest.mark.django_db
class TestUserAchievementList:
    """Tests pour GET /api/achievements/mine/."""

    def test_unauthenticated_returns_401(self, api_client):
        url = reverse("user-achievement-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_list_for_new_user(self, auth_client):
        url = reverse("user-achievement-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == [] or response.data.get("results", []) == []

    def test_returns_earned_achievement(self, auth_client, user, achievement):
        UserAchievement.objects.create(user=user, achievement=achievement)
        url = reverse("user-achievement-list")
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        results = (
            response.data
            if isinstance(response.data, list)
            else response.data.get("results", [])
        )
        assert len(results) == 1


@pytest.mark.django_db
class TestUserAchievementUniqueness:
    """Vérifie l'unicité du couple (user, achievement)."""

    def test_duplicate_raises_integrity_error(self, user, achievement):
        from django.db import IntegrityError

        UserAchievement.objects.create(user=user, achievement=achievement)
        with pytest.raises(IntegrityError):
            UserAchievement.objects.create(user=user, achievement=achievement)


@pytest.mark.django_db
class TestUserAchievementsByUser:
    """Tests pour GET /api/achievements/user/<user_id>/."""

    def test_returns_achievements_for_any_authenticated_user(
        self, auth_client, user2, achievement
    ):
        UserAchievement.objects.create(user=user2, achievement=achievement)
        url = reverse(
            "user-achievements-by-user", kwargs={"user_id": user2.pk}
        )
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
