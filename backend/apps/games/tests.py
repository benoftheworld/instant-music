"""
Tests complets pour l'application games.

Couvre : creation, join/leave, permissions hôte, start, answer,
end round, next round, public games, history.
"""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.games.models import Game, GameAnswer, GamePlayer, GameRound

User = get_user_model()


def _make_game(host, **kwargs):
    """Crée un jeu avec un room_code unique."""
    import random
    import string

    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
    defaults = {
        "room_code": code,
        "mode": "classique",
        "playlist_id": "123456",
        "playlist_name": "Test Playlist",
    }
    defaults.update(kwargs)
    game = Game.objects.create(host=host, **defaults)
    GamePlayer.objects.create(game=game, user=host)
    return game


def _make_round(game, round_number=1, started=True):
    """Crée un round pour un jeu."""
    return GameRound.objects.create(
        game=game,
        round_number=round_number,
        track_id="track_1",
        track_name="Test Song",
        artist_name="Test Artist",
        correct_answer="Test Song",
        options=["Test Song", "Wrong 1", "Wrong 2", "Wrong 3"],
        preview_url="https://example.com/preview.mp3",
        started_at=timezone.now() if started else None,
    )


# ── Modèle Game ──────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGameModel:
    """Tests du modèle Game."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="host", email="host@example.com", password="Str0ngP@ss!"
        )

    def test_game_creation(self):
        game = Game.objects.create(
            host=self.user, room_code="ABC123", mode="classique"
        )
        assert game.room_code == "ABC123"
        assert game.host == self.user
        assert game.status == "waiting"

    def test_game_default_values(self):
        game = Game.objects.create(
            host=self.user, room_code="DEF456", mode="classique"
        )
        assert game.max_players == 8
        assert game.num_rounds == 10
        assert game.round_duration == 30

    def test_add_player(self):
        game = Game.objects.create(
            host=self.user, room_code="GHI789", mode="classique"
        )
        player = GamePlayer.objects.create(game=game, user=self.user)
        assert game.players.count() == 1
        assert player.score == 0
        assert player.consecutive_correct == 0

    def test_unique_player_per_game(self):
        game = Game.objects.create(
            host=self.user, room_code="JKL012", mode="classique"
        )
        GamePlayer.objects.create(game=game, user=self.user)
        with pytest.raises(Exception):
            GamePlayer.objects.create(game=game, user=self.user)


# ── Création de partie ───────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGameCreate:
    """Tests de création de partie via API."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="creator",
            email="creator@example.com",
            password="Str0ngP@ss!",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_game(self):
        data = {
            "mode": "classique",
            "playlist_id": "123456",
            "playlist_name": "Ma Playlist",
        }
        response = self.client.post("/api/games/", data)
        assert response.status_code == status.HTTP_201_CREATED
        assert "room_code" in response.data
        assert response.data["status"] == "waiting"

    def test_create_game_host_auto_joined(self):
        data = {"mode": "classique", "playlist_id": "123456"}
        response = self.client.post("/api/games/", data)
        assert response.status_code == status.HTTP_201_CREATED
        game = Game.objects.get(room_code=response.data["room_code"])
        assert GamePlayer.objects.filter(game=game, user=self.user).exists()

    def test_create_game_unauthenticated(self):
        client = APIClient()
        data = {"mode": "classique", "playlist_id": "123456"}
        response = client.post("/api/games/", data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ── Rejoindre / quitter ──────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGameJoinLeave:
    """Tests de join/leave de partie."""

    def setup_method(self):
        self.host = User.objects.create_user(
            username="host", email="host@example.com", password="Str0ngP@ss!"
        )
        self.player = User.objects.create_user(
            username="player",
            email="player@example.com",
            password="Str0ngP@ss!",
        )
        self.game = _make_game(self.host)
        self.host_client = APIClient()
        self.host_client.force_authenticate(user=self.host)
        self.player_client = APIClient()
        self.player_client.force_authenticate(user=self.player)

    @patch("apps.games.views.game_viewset.broadcast_player_join")
    def test_join_game(self, mock_broadcast):
        url = f"/api/games/{self.game.room_code}/join/"
        response = self.player_client.post(url)
        assert response.status_code == status.HTTP_201_CREATED
        assert GamePlayer.objects.filter(
            game=self.game, user=self.player
        ).exists()

    @patch("apps.games.views.game_viewset.broadcast_player_join")
    def test_join_already_joined(self, mock_broadcast):
        GamePlayer.objects.create(game=self.game, user=self.player)
        url = f"/api/games/{self.game.room_code}/join/"
        response = self.player_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.games.views.game_viewset.broadcast_player_join")
    def test_join_game_full(self, mock_broadcast):
        self.game.max_players = 1
        self.game.save()
        url = f"/api/games/{self.game.room_code}/join/"
        response = self.player_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.games.views.game_viewset.broadcast_player_join")
    def test_join_game_not_waiting(self, mock_broadcast):
        self.game.status = "in_progress"
        self.game.save()
        url = f"/api/games/{self.game.room_code}/join/"
        response = self.player_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("apps.games.views.game_viewset.broadcast_player_leave")
    def test_player_leave(self, mock_broadcast):
        GamePlayer.objects.create(game=self.game, user=self.player)
        url = f"/api/games/{self.game.room_code}/leave/"
        response = self.player_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        assert not GamePlayer.objects.filter(
            game=self.game, user=self.player
        ).exists()

    @patch("apps.games.views.game_viewset.broadcast_player_leave")
    def test_host_leave_cancels_game(self, mock_broadcast):
        url = f"/api/games/{self.game.room_code}/leave/"
        response = self.host_client.post(url)
        assert response.status_code == status.HTTP_200_OK
        self.game.refresh_from_db()
        assert self.game.status == "cancelled"

    def test_leave_not_in_game(self):
        url = f"/api/games/{self.game.room_code}/leave/"
        response = self.player_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Permissions hôte ─────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestHostPermissions:
    """Tests des actions réservées à l'hôte."""

    def setup_method(self):
        self.host = User.objects.create_user(
            username="host", email="host@example.com", password="Str0ngP@ss!"
        )
        self.other = User.objects.create_user(
            username="other", email="other@example.com", password="Str0ngP@ss!"
        )
        self.game = _make_game(self.host)
        GamePlayer.objects.create(game=self.game, user=self.other)
        self.game.status = "in_progress"
        self.game.save()
        _make_round(self.game, round_number=1, started=True)

        self.other_client = APIClient()
        self.other_client.force_authenticate(user=self.other)

    def test_non_host_cannot_start(self):
        self.game.status = "waiting"
        self.game.save()
        url = f"/api/games/{self.game.room_code}/start/"
        response = self.other_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_host_cannot_end_round(self):
        url = f"/api/games/{self.game.room_code}/end-round/"
        response = self.other_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_non_host_cannot_next_round(self):
        url = f"/api/games/{self.game.room_code}/next-round/"
        response = self.other_client.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ── Soumission de réponse ────────────────────────────────────────────────────


@pytest.mark.django_db
class TestAnswerSubmission:
    """Tests de soumission de réponse."""

    def setup_method(self):
        self.host = User.objects.create_user(
            username="host", email="host@example.com", password="Str0ngP@ss!"
        )
        self.player_user = User.objects.create_user(
            username="player",
            email="player@example.com",
            password="Str0ngP@ss!",
        )
        self.game = _make_game(self.host)
        self.game.status = "in_progress"
        self.game.save()
        self.player = GamePlayer.objects.create(
            game=self.game, user=self.player_user
        )
        self.round = _make_round(self.game, round_number=1, started=True)

        self.client = APIClient()
        self.client.force_authenticate(user=self.player_user)

    @patch("apps.games.views.game_viewset.broadcast_round_end")
    def test_answer_success(self, mock_broadcast):
        url = f"/api/games/{self.game.room_code}/answer/"
        data = {"answer": "Test Song", "response_time": 5.0}
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        assert GameAnswer.objects.filter(
            round=self.round, player=self.player
        ).exists()

    @patch("apps.games.views.game_viewset.broadcast_round_end")
    def test_answer_duplicate(self, mock_broadcast):
        GameAnswer.objects.create(
            round=self.round,
            player=self.player,
            answer="Test Song",
            response_time=5.0,
        )
        url = f"/api/games/{self.game.room_code}/answer/"
        data = {"answer": "Another Answer", "response_time": 3.0}
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_answer_empty(self):
        url = f"/api/games/{self.game.room_code}/answer/"
        data = {"answer": "", "response_time": 5.0}
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_answer_not_in_game(self):
        outsider = User.objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password="Str0ngP@ss!",
        )
        client = APIClient()
        client.force_authenticate(user=outsider)
        url = f"/api/games/{self.game.room_code}/answer/"
        data = {"answer": "Test Song", "response_time": 5.0}
        response = client.post(url, data)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_answer_no_active_round(self):
        self.round.ended_at = timezone.now()
        self.round.save()
        url = f"/api/games/{self.game.room_code}/answer/"
        data = {"answer": "Test Song", "response_time": 5.0}
        response = self.client.post(url, data)
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Parties publiques et historique ──────────────────────────────────────────


@pytest.mark.django_db
class TestPublicGamesAndHistory:
    """Tests des endpoints publics : public_games et history."""

    def setup_method(self):
        self.user = User.objects.create_user(
            username="viewer",
            email="viewer@example.com",
            password="Str0ngP@ss!",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_public_games_listed(self):
        host = User.objects.create_user(
            username="pubhost",
            email="pubhost@example.com",
            password="Str0ngP@ss!",
        )
        _make_game(host, is_public=True, is_online=True)
        response = self.client.get("/api/games/public/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1

    def test_private_games_not_listed(self):
        host = User.objects.create_user(
            username="privhost",
            email="privhost@example.com",
            password="Str0ngP@ss!",
        )
        _make_game(host, is_public=False, is_online=True)
        response = self.client.get("/api/games/public/")
        assert response.status_code == status.HTTP_200_OK
        codes = [g["room_code"] for g in response.data]
        assert not any(
            Game.objects.filter(room_code=c, is_public=False).exists()
            for c in codes
        )

    def test_history_returns_finished_games(self):
        host = User.objects.create_user(
            username="histhost",
            email="histhost@example.com",
            password="Str0ngP@ss!",
        )
        game = _make_game(host)
        game.status = "finished"
        game.finished_at = timezone.now()
        game.save()
        response = self.client.get("/api/games/history/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["count"] >= 1


# ── Résultats ────────────────────────────────────────────────────────────────


@pytest.mark.django_db
class TestGameResults:
    """Tests de l'endpoint résultats."""

    def setup_method(self):
        self.host = User.objects.create_user(
            username="host", email="host@example.com", password="Str0ngP@ss!"
        )
        self.game = _make_game(self.host)
        self.game.status = "finished"
        self.game.finished_at = timezone.now()
        self.game.save()

        self.client = APIClient()
        self.client.force_authenticate(user=self.host)

    def test_results_as_participant(self):
        url = f"/api/games/{self.game.room_code}/results/"
        response = self.client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert "rankings" in response.data
        assert "game" in response.data

    def test_results_as_non_participant(self):
        outsider = User.objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password="Str0ngP@ss!",
        )
        client = APIClient()
        client.force_authenticate(user=outsider)
        url = f"/api/games/{self.game.room_code}/results/"
        response = client.get(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
