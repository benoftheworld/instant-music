"""
Tests complets pour l'application users.

Couvre : modèle utilisateur, profil (me), changement de mot de passe,
suppression de compte (RGPD), export de données (RGPD), recherche,
amitiés (envoi, acceptation, refus, suppression).
"""

import json

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.users.models import Friendship, FriendshipStatus

User = get_user_model()


# ── Modèle User ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserModel:
    """Tests du modèle User."""

    def test_user_creation(self):
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="Str0ngP@ss!",
        )
        assert user.username == "testuser"
        assert user.check_password("Str0ngP@ss!")

    def test_email_hash_generated(self):
        user = User.objects.create_user(
            username="hashuser",
            email="hash@example.com",
            password="Str0ngP@ss!",
        )
        assert user.email_hash is not None
        assert len(user.email_hash) > 0

    def test_get_by_email(self):
        User.objects.create_user(
            username="lookup",
            email="lookup@example.com",
            password="Str0ngP@ss!",
        )
        found = User.objects.get_by_email("lookup@example.com")
        assert found.username == "lookup"

    def test_win_rate_zero_games(self):
        user = User.objects.create_user(
            username="newbie",
            email="newbie@example.com",
            password="Str0ngP@ss!",
        )
        assert user.win_rate == 0.0

    def test_win_rate_calculation(self):
        user = User.objects.create_user(
            username="gamer",
            email="gamer@example.com",
            password="Str0ngP@ss!",
        )
        user.total_games_played = 10
        user.total_wins = 3
        user.save()
        assert user.win_rate == 30.0

    def test_default_coins_balance(self):
        user = User.objects.create_user(
            username="coinuser",
            email="coin@example.com",
            password="Str0ngP@ss!",
        )
        assert user.coins_balance == 0


# ── Profil (me) ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserProfile:
    """Tests de l'endpoint /users/me/."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="profileuser",
            email="profile@example.com",
            password="Str0ngP@ss!",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_me(self):
        response = self.client.get("/api/users/me/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["username"] == "profileuser"
        assert "email" in response.data
        assert "total_games_played" in response.data

    def test_get_me_unauthenticated(self):
        client = APIClient()
        response = client.get("/api/users/me/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_patch_me(self):
        """PATCH /users/me/ permet de mettre à jour le profil."""
        response = self.client.patch("/api/users/me/", {}, format="json")
        assert response.status_code == status.HTTP_200_OK


# ── Changement de mot de passe ───────────────────────────────────────────────


@pytest.mark.django_db
class TestChangePassword:
    """Tests du changement de mot de passe."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="pwduser",
            email="pwd@example.com",
            password="OldStr0ng!Pass",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/users/change_password/"

    def test_change_password_success(self):
        data = {
            "old_password": "OldStr0ng!Pass",
            "new_password": "NewStr0ng!Pass",
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_200_OK
        self.user.refresh_from_db()
        assert self.user.check_password("NewStr0ng!Pass")

    def test_change_password_wrong_old(self):
        data = {
            "old_password": "WrongOld!Pass1",
            "new_password": "NewStr0ng!Pass",
        }
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_change_password_missing_fields(self):
        response = self.client.post(self.url, {})
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Suppression de compte (RGPD) ────────────────────────────────────────────


@pytest.mark.django_db
class TestDeleteAccount:
    """Tests de suppression de compte (RGPD art. 17)."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="deleteuser",
            email="delete@example.com",
            password="Str0ngP@ss!",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/users/delete_account/"

    def test_delete_account(self):
        user_id = self.user.id
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert not User.objects.filter(id=user_id).exists()

    def test_delete_account_unauthenticated(self):
        client = APIClient()
        response = client.delete(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── Export de données (RGPD) ─────────────────────────────────────────────────


@pytest.mark.django_db
class TestExportData:
    """Tests de l'export de données personnelles (RGPD art. 20)."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="exportuser",
            email="export@example.com",
            password="Str0ngP@ss!",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = "/api/users/export_data/"

    def test_export_data_returns_json(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response["Content-Type"] == "application/json"
        data = json.loads(response.content)
        assert "profile" in data
        assert data["profile"]["username"] == "exportuser"

    def test_export_data_contains_required_sections(self):
        response = self.client.get(self.url)
        data = json.loads(response.content)
        assert "exported_at" in data
        assert "profile" in data
        assert "game_participations" in data
        assert "game_answers" in data
        assert "achievements" in data
        assert "teams" in data
        assert "inventory" in data
        assert "friends" in data

    def test_export_data_unauthenticated(self):
        client = APIClient()
        response = client.get(self.url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── Recherche ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestUserSearch:
    """Tests de la recherche d'utilisateurs."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="searcher",
            email="searcher@example.com",
            password="Str0ngP@ss!",
        )
        User.objects.create_user(
            username="alice",
            email="alice@example.com",
            password="Str0ngP@ss!",
        )
        User.objects.create_user(
            username="bob",
            email="bob@example.com",
            password="Str0ngP@ss!",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_search_by_username(self):
        response = self.client.get("/api/users/search/?q=ali")
        assert response.status_code == status.HTTP_200_OK
        usernames = [u["username"] for u in response.data]
        assert "alice" in usernames

    def test_search_excludes_self(self):
        response = self.client.get("/api/users/search/?q=searcher")
        assert response.status_code == status.HTTP_200_OK
        usernames = [u["username"] for u in response.data]
        assert "searcher" not in usernames

    def test_search_too_short(self):
        response = self.client.get("/api/users/search/?q=a")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0


# ── Amitiés ──────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestFriendships:
    """Tests du système d'amitié."""

    def setup_method(self):
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@example.com",
            password="Str0ngP@ss!",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="Str0ngP@ss!",
        )
        self.client1 = APIClient()
        self.client1.force_authenticate(user=self.user1)
        self.client2 = APIClient()
        self.client2.force_authenticate(user=self.user2)

    def test_send_friend_request(self):
        response = self.client1.post(
            "/api/users/friends/send_request/",
            {"username": "user2"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert Friendship.objects.filter(
            from_user=self.user1,
            to_user=self.user2,
            status=FriendshipStatus.PENDING,
        ).exists()

    def test_send_friend_request_to_self(self):
        response = self.client1.post(
            "/api/users/friends/send_request/",
            {"username": "user1"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_send_friend_request_nonexistent_user(self):
        response = self.client1.post(
            "/api/users/friends/send_request/",
            {"username": "ghost"},
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_accept_friend_request(self):
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status=FriendshipStatus.PENDING,
        )
        response = self.client2.post(
            f"/api/users/friends/{friendship.id}/accept/"
        )
        assert response.status_code == status.HTTP_200_OK
        friendship.refresh_from_db()
        assert friendship.status == FriendshipStatus.ACCEPTED

    def test_reject_friend_request(self):
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status=FriendshipStatus.PENDING,
        )
        response = self.client2.post(
            f"/api/users/friends/{friendship.id}/reject/"
        )
        assert response.status_code == status.HTTP_200_OK
        friendship.refresh_from_db()
        assert friendship.status == FriendshipStatus.REJECTED

    def test_list_friends(self):
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status=FriendshipStatus.ACCEPTED,
        )
        response = self.client1.get("/api/users/friends/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_pending_requests(self):
        Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status=FriendshipStatus.PENDING,
        )
        response = self.client2.get("/api/users/friends/pending/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_remove_friend(self):
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status=FriendshipStatus.ACCEPTED,
        )
        response = self.client1.delete(
            f"/api/users/friends/{friendship.id}/remove/"
        )
        assert response.status_code == status.HTTP_200_OK
        assert not Friendship.objects.filter(id=friendship.id).exists()

    def test_cannot_accept_others_request(self):
        """Un utilisateur ne peut accepter que les requêtes qui lui sont destinées."""
        friendship = Friendship.objects.create(
            from_user=self.user1,
            to_user=self.user2,
            status=FriendshipStatus.PENDING,
        )
        # user1 essaie d'accepter sa propre requête
        response = self.client1.post(
            f"/api/users/friends/{friendship.id}/accept/"
        )
        assert response.status_code in (
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        )
