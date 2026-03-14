"""Tests d'intégration des GameViewSet mixins."""

import pytest
from rest_framework import status

from tests.base import BaseAPIIntegrationTest


@pytest.mark.django_db
class TestGameLobbyMixin(BaseAPIIntegrationTest):
    """Vérifie les actions lobby: create, join, leave, start."""

    def get_base_url(self):
        return "/api/games/"

    def test_create_game(self, auth_client, user):
        """Créer une partie avec données minimales."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test Playlist",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, status.HTTP_201_CREATED)
        assert "room_code" in resp.data

    def test_create_game_unauthenticated(self, api_client):
        """Créer une partie sans authentification échoue."""
        resp = api_client.post(self.get_base_url(), {}, format="json")
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)

    def test_join_game(self, auth_client, auth_client2, user, user2):
        """Rejoindre une partie existante."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp2 = auth_client2.post(f"{self.get_base_url()}{room_code}/join/")
        self.assert_status(resp2, status.HTTP_201_CREATED)

    def test_join_nonexistent_game(self, auth_client):
        """Rejoindre une partie inexistante échoue."""
        resp = auth_client.post(f"{self.get_base_url()}XXXXX/join/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)

    def test_leave_game(self, auth_client, auth_client2, user, user2):
        """Quitter une partie."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        auth_client2.post(f"{self.get_base_url()}{room_code}/join/")
        resp = auth_client2.post(f"{self.get_base_url()}{room_code}/leave/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_host_leave_cancels_game(self, auth_client, user):
        """L'hôte quitte → partie annulée."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client.post(f"{self.get_base_url()}{room_code}/leave/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_start_game_not_enough_players(self, auth_client, user):
        """Démarrer une partie sans assez de joueurs échoue."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
            "is_online": True,
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client.post(f"{self.get_base_url()}{room_code}/start/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_game(self, auth_client, user):
        """Récupérer une partie par room_code."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client.get(f"{self.get_base_url()}{room_code}/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data["room_code"] == room_code


@pytest.mark.django_db
class TestGameDiscoveryMixin(BaseAPIIntegrationTest):
    """Vérifie les actions discovery: public, history, leaderboard."""

    def get_base_url(self):
        return "/api/games/"

    def test_public_games(self, auth_client):
        """Lister les parties publiques."""
        resp = auth_client.get(f"{self.get_base_url()}public/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert "results" in resp.data

    def test_history_unauthenticated(self, api_client):
        """L'historique est accessible sans authentification."""
        resp = api_client.get(f"{self.get_base_url()}history/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_history_with_mode_filter(self, api_client):
        """Filtre par mode."""
        resp = api_client.get(f"{self.get_base_url()}history/?mode=classique")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_leaderboard(self, api_client):
        """Le classement global est accessible sans authentification."""
        resp = api_client.get(f"{self.get_base_url()}leaderboard/")
        self.assert_status(resp, status.HTTP_200_OK)


@pytest.mark.django_db
class TestGameRoundMixin(BaseAPIIntegrationTest):
    """Vérifie les actions round: current-round, answer, end-round, next-round."""

    def get_base_url(self):
        return "/api/games/"

    def test_current_round_not_in_game(self, auth_client, auth_client2, user, user2):
        """Accéder au round courant sans être dans la partie → 403."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client2.get(f"{self.get_base_url()}{room_code}/current-round/")
        self.assert_status(resp, status.HTTP_403_FORBIDDEN)

    def test_answer_not_in_game(self, auth_client, auth_client2, user, user2):
        """Répondre sans être dans la partie → 403."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client2.post(
            f"{self.get_base_url()}{room_code}/answer/",
            {"answer": "test"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_403_FORBIDDEN)

    def test_answer_no_active_round(self, auth_client, user):
        """Répondre sans round actif → 400."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client.post(
            f"{self.get_base_url()}{room_code}/answer/",
            {"answer": "test"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_answer_empty(self, auth_client, user):
        """Répondre avec une réponse vide → 400."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client.post(
            f"{self.get_base_url()}{room_code}/answer/",
            {"answer": ""},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestGameResultsMixin(BaseAPIIntegrationTest):
    """Vérifie les actions results: results, results/pdf."""

    def get_base_url(self):
        return "/api/games/"

    def test_results_not_in_game(self, auth_client, auth_client2, user, user2):
        """Accéder aux résultats sans être dans la partie → 403."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client2.get(f"{self.get_base_url()}{room_code}/results/")
        self.assert_status(resp, status.HTTP_403_FORBIDDEN)

    def test_results_pdf_not_in_game(self, auth_client, auth_client2, user, user2):
        """Télécharger le PDF sans être dans la partie → 403."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client2.get(f"{self.get_base_url()}{room_code}/results/pdf/")
        self.assert_status(resp, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
class TestGameInvitationMixin(BaseAPIIntegrationTest):
    """Vérifie les actions invitation: invite, my-invitations, accept, decline."""

    def get_base_url(self):
        return "/api/games/"

    def test_my_invitations(self, auth_client):
        """Récupérer ses invitations (vide)."""
        resp = auth_client.get(f"{self.get_base_url()}my-invitations/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_decline_nonexistent(self, auth_client):
        """Refuser une invitation inexistante → 404."""
        import uuid

        fake_id = str(uuid.uuid4())
        resp = auth_client.post(f"{self.get_base_url()}invitations/{fake_id}/decline/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)

    def test_accept_nonexistent(self, auth_client):
        """Accepter une invitation inexistante → 404."""
        import uuid

        fake_id = str(uuid.uuid4())
        resp = auth_client.post(f"{self.get_base_url()}invitations/{fake_id}/accept/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)

    def test_invite_no_username(self, auth_client, user):
        """Inviter sans username → 400."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client.post(
            f"{self.get_base_url()}{room_code}/invite/",
            {},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_invite_self(self, auth_client, user):
        """S'inviter soi-même → 400."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client.post(
            f"{self.get_base_url()}{room_code}/invite/",
            {"username": user.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_invite_user_not_found(self, auth_client, user):
        """Inviter un utilisateur inexistant → 404."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client.post(
            f"{self.get_base_url()}{room_code}/invite/",
            {"username": "nonexistent_user_xyz"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)

    def test_invite_success(self, auth_client, auth_client2, user, user2):
        """Inviter un utilisateur valide → 201."""
        data = {
            "mode": "classique",
            "num_rounds": 5,
            "round_duration": 30,
            "playlist_id": "123456",
            "playlist_name": "Test",
            "answer_mode": "mcq",
            "guess_target": "title",
        }
        resp = auth_client.post(self.get_base_url(), data, format="json")
        room_code = resp.data["room_code"]

        resp = auth_client.post(
            f"{self.get_base_url()}{room_code}/invite/",
            {"username": user2.username},
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)
