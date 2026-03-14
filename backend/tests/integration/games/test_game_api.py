"""Tests d'intégration de l'API Game."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestGameCreate(BaseAPIIntegrationTest):
    """Vérifie la création de partie."""

    def get_base_url(self):
        return "/api/games/"

    def test_create_game_success(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.post(
            self.get_base_url(),
            {
                "mode": "classique",
                "playlist_id": "123456",
                "max_players": 8,
                "num_rounds": 10,
            },
            format="json",
        )
        self.assert_status(resp, 201)
        assert "room_code" in resp.data

    def test_create_game_unauthenticated(self):
        client = self.get_client()
        resp = client.post(
            self.get_base_url(),
            {"mode": "classique", "playlist_id": "123"},
            format="json",
        )
        self.assert_status(resp, 401)


class TestGameRetrieve(BaseAPIIntegrationTest):
    """Vérifie la récupération d'une partie."""

    def get_base_url(self):
        return "/api/games/"

    def test_retrieve_game(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        # Créer via l'API pour obtenir un room_code valide
        resp = client.post(
            self.get_base_url(),
            {
                "mode": "classique",
                "playlist_id": "123456",
                "max_players": 8,
                "num_rounds": 10,
            },
            format="json",
        )
        room_code = resp.data["room_code"]
        resp = client.get(f"{self.get_base_url()}{room_code}/")
        self.assert_status(resp, 200)
        assert resp.data["room_code"] == room_code

    def test_retrieve_nonexistent(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(f"{self.get_base_url()}ZZZZZZ/")
        self.assert_status(resp, 404)
