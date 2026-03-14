"""Tests d'intégration approfondis des Game ViewSet mixins (round, lobby, invitation, results, discovery)."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone
from rest_framework import status

from tests.base import BaseAPIIntegrationTest
from tests.factories import (
    GameAnswerFactory,
    GameFactory,
    GameInvitationFactory,
    GamePlayerFactory,
    GameRoundFactory,
    UserFactory,
)


BASE = "/api/games/"


# ═══════════════════════════════════════════════════════════════════
#  GameRoundMixin — tests approfondis
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestCurrentRoundWithRounds(BaseAPIIntegrationTest):
    """GET /{room_code}/current-round/ — avec rounds."""

    def get_base_url(self):
        return BASE

    def test_current_round_exists(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        GameRoundFactory(
            game=game,
            round_number=1,
            started_at=timezone.now(),
            ended_at=None,
        )
        resp = auth_client.get(f"{BASE}{game.room_code}/current-round/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data["current_round"] is not None

    def test_current_round_game_finished(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        GameRoundFactory(
            game=game,
            round_number=1,
            started_at=timezone.now(),
            ended_at=timezone.now(),
        )
        resp = auth_client.get(f"{BASE}{game.room_code}/current-round/")
        self.assert_status(resp, status.HTTP_200_OK)
        # No current round (all ended), no next round → partie terminée
        assert resp.data.get("current_round") is None

    def test_current_round_with_next(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        # Round 1 ended
        GameRoundFactory(
            game=game, round_number=1, started_at=timezone.now(), ended_at=timezone.now()
        )
        # Round 2 not started
        GameRoundFactory(
            game=game, round_number=2, started_at=None, ended_at=None
        )
        resp = auth_client.get(f"{BASE}{game.room_code}/current-round/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data.get("next_round") is not None


@pytest.mark.django_db
class TestAnswerSubmission(BaseAPIIntegrationTest):
    """POST /{room_code}/answer/ — soumission de réponses."""

    def get_base_url(self):
        return BASE

    def test_answer_success(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        player = GamePlayerFactory(game=game, user=user)
        round_obj = GameRoundFactory(
            game=game,
            round_number=1,
            started_at=timezone.now(),
            ended_at=None,
            correct_answer="Option A",
            options=["Option A", "Option B", "Option C", "Option D"],
        )
        resp = auth_client.post(
            f"{BASE}{game.room_code}/answer/",
            {"answer": "Option A"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)

    def test_answer_duplicate(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        player = GamePlayerFactory(game=game, user=user)
        round_obj = GameRoundFactory(
            game=game, round_number=1, started_at=timezone.now(), ended_at=None,
            correct_answer="A", options=["A", "B", "C", "D"],
        )
        GameAnswerFactory(round=round_obj, player=player, answer="A")
        resp = auth_client.post(
            f"{BASE}{game.room_code}/answer/",
            {"answer": "B"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestEndRound(BaseAPIIntegrationTest):
    """POST /{room_code}/end-round/ — terminer le round (hôte)."""

    def get_base_url(self):
        return BASE

    @patch("apps.games.views.game_round_mixin.broadcast_round_end")
    def test_end_round_success(self, mock_broadcast, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        GameRoundFactory(
            game=game, round_number=1, started_at=timezone.now(), ended_at=None,
            correct_answer="Song A",
        )
        resp = auth_client.post(f"{BASE}{game.room_code}/end-round/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data["correct_answer"] == "Song A"

    def test_end_round_no_active(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        resp = auth_client.post(f"{BASE}{game.room_code}/end-round/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_end_round_already_ended(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        GameRoundFactory(
            game=game, round_number=1,
            started_at=timezone.now(), ended_at=timezone.now(),
        )
        # All rounds ended → get_current_round returns None → 400
        resp = auth_client.post(f"{BASE}{game.room_code}/end-round/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_end_round_not_host(self, auth_client2, user, user2):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        GamePlayerFactory(game=game, user=user2)
        GameRoundFactory(
            game=game, round_number=1, started_at=timezone.now(), ended_at=None,
        )
        resp = auth_client2.post(f"{BASE}{game.room_code}/end-round/")
        self.assert_status(resp, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
class TestNextRound(BaseAPIIntegrationTest):
    """POST /{room_code}/next-round/ — round suivant (hôte)."""

    def get_base_url(self):
        return BASE

    @patch("apps.games.views.game_round_mixin.broadcast_next_round")
    @patch("apps.games.views.game_round_mixin.broadcast_round_end")
    def test_next_round_advance(self, mock_end, mock_next, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        GameRoundFactory(
            game=game, round_number=1,
            started_at=timezone.now(), ended_at=timezone.now(),
        )
        GameRoundFactory(
            game=game, round_number=2, started_at=None, ended_at=None,
        )
        resp = auth_client.post(f"{BASE}{game.room_code}/next-round/")
        self.assert_status(resp, status.HTTP_200_OK)
        mock_next.assert_called_once()

    @patch("apps.games.views.game_round_mixin.broadcast_game_finish")
    @patch("apps.games.views.game_round_mixin.broadcast_round_end")
    def test_next_round_finish_game(self, mock_end, mock_finish, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        GameRoundFactory(
            game=game, round_number=1,
            started_at=timezone.now(), ended_at=timezone.now(),
        )
        # No more rounds → game should finish
        resp = auth_client.post(f"{BASE}{game.room_code}/next-round/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert "terminée" in resp.data.get("message", "")


# ═══════════════════════════════════════════════════════════════════
#  GameLobbyMixin — tests approfondis
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestLobbyJoinEdgeCases(BaseAPIIntegrationTest):
    """POST /{room_code}/join/ — cas limites."""

    def get_base_url(self):
        return BASE

    def test_join_game_already_started(self, auth_client2, user, user2):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        resp = auth_client2.post(f"{BASE}{game.room_code}/join/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)
        assert "commencé" in resp.data["error"]

    def test_join_game_full(self, auth_client2, user, user2):
        game = GameFactory(host=user, status="waiting", max_players=1)
        GamePlayerFactory(game=game, user=user)
        resp = auth_client2.post(f"{BASE}{game.room_code}/join/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)
        assert "pleine" in resp.data["error"]

    def test_join_game_already_in(self, auth_client, user):
        game = GameFactory(host=user, status="waiting")
        GamePlayerFactory(game=game, user=user)
        resp = auth_client.post(f"{BASE}{game.room_code}/join/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)
        assert "déjà" in resp.data["error"]


@pytest.mark.django_db
class TestLobbyPatchAndLeave(BaseAPIIntegrationTest):
    """PATCH + leave edge cases."""

    def get_base_url(self):
        return BASE

    @patch("apps.games.views.game_lobby_mixin.broadcast_game_update")
    def test_partial_update(self, mock_broadcast, auth_client, user):
        game = GameFactory(host=user, status="waiting")
        GamePlayerFactory(game=game, user=user)
        resp = auth_client.patch(
            f"{BASE}{game.room_code}/",
            {"max_players": 4},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)
        mock_broadcast.assert_called_once()

    def test_leave_in_progress_fails(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        resp = auth_client.post(f"{BASE}{game.room_code}/leave/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_leave_not_in_game(self, auth_client2, user, user2):
        game = GameFactory(host=user, status="waiting")
        GamePlayerFactory(game=game, user=user)
        resp = auth_client2.post(f"{BASE}{game.room_code}/leave/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestLobbyStartEdgeCases(BaseAPIIntegrationTest):
    """POST /{room_code}/start/ — cas limites."""

    def get_base_url(self):
        return BASE

    def test_start_already_in_progress(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        GameRoundFactory(game=game, round_number=1)
        resp = auth_client.post(f"{BASE}{game.room_code}/start/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data["rounds_created"] >= 1


# ═══════════════════════════════════════════════════════════════════
#  GameInvitationMixin — tests approfondis
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestInviteSuccess(BaseAPIIntegrationTest):
    """POST /{room_code}/invite/ — invitation réussie."""

    def get_base_url(self):
        return BASE

    def test_invite_success(self, auth_client, user):
        game = GameFactory(host=user, status="waiting")
        GamePlayerFactory(game=game, user=user)
        target = UserFactory(username="invitee")
        resp = auth_client.post(
            f"{BASE}{game.room_code}/invite/",
            {"username": "invitee"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_201_CREATED)

    def test_invite_game_full(self, auth_client, user):
        game = GameFactory(host=user, status="waiting", max_players=1)
        GamePlayerFactory(game=game, user=user)
        target = UserFactory(username="invitee2")
        resp = auth_client.post(
            f"{BASE}{game.room_code}/invite/",
            {"username": "invitee2"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_invite_already_in_game(self, auth_client, user):
        game = GameFactory(host=user, status="waiting", max_players=8)
        GamePlayerFactory(game=game, user=user)
        target = UserFactory(username="invitee3")
        GamePlayerFactory(game=game, user=target)
        resp = auth_client.post(
            f"{BASE}{game.room_code}/invite/",
            {"username": "invitee3"},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestAcceptDeclineInvitation(BaseAPIIntegrationTest):
    """Accepter/refuser invitation."""

    def get_base_url(self):
        return BASE

    def test_accept_invitation_success(self, auth_client2, user, user2):
        game = GameFactory(host=user, status="waiting", max_players=8)
        GamePlayerFactory(game=game, user=user)
        invitation = GameInvitationFactory(
            game=game, sender=user, recipient=user2, status="pending"
        )
        # Ensure not expired
        invitation.expires_at = timezone.now() + timedelta(hours=1)
        invitation.save(update_fields=["expires_at"])

        resp = auth_client2.post(f"{BASE}invitations/{invitation.id}/accept/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert "room_code" in resp.data

    def test_accept_invitation_expired(self, auth_client2, user, user2):
        game = GameFactory(host=user, status="waiting", max_players=8)
        GamePlayerFactory(game=game, user=user)
        invitation = GameInvitationFactory(
            game=game, sender=user, recipient=user2, status="pending"
        )
        invitation.expires_at = timezone.now() - timedelta(hours=1)
        invitation.save(update_fields=["expires_at"])

        resp = auth_client2.post(f"{BASE}invitations/{invitation.id}/accept/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)
        assert "expiré" in resp.data["error"]

    def test_accept_invitation_already_accepted(self, auth_client2, user, user2):
        game = GameFactory(host=user, status="waiting", max_players=8)
        GamePlayerFactory(game=game, user=user)
        invitation = GameInvitationFactory(
            game=game, sender=user, recipient=user2, status="accepted"
        )
        resp = auth_client2.post(f"{BASE}invitations/{invitation.id}/accept/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_decline_invitation_success(self, auth_client2, user, user2):
        game = GameFactory(host=user, status="waiting")
        invitation = GameInvitationFactory(
            game=game, sender=user, recipient=user2, status="pending"
        )
        resp = auth_client2.post(f"{BASE}invitations/{invitation.id}/decline/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_accept_game_not_waiting(self, auth_client2, user, user2):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        invitation = GameInvitationFactory(
            game=game, sender=user, recipient=user2, status="pending"
        )
        invitation.expires_at = timezone.now() + timedelta(hours=1)
        invitation.save(update_fields=["expires_at"])
        resp = auth_client2.post(f"{BASE}invitations/{invitation.id}/accept/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_accept_game_full(self, auth_client2, user, user2):
        game = GameFactory(host=user, status="waiting", max_players=1)
        GamePlayerFactory(game=game, user=user)
        invitation = GameInvitationFactory(
            game=game, sender=user, recipient=user2, status="pending"
        )
        invitation.expires_at = timezone.now() + timedelta(hours=1)
        invitation.save(update_fields=["expires_at"])
        resp = auth_client2.post(f"{BASE}invitations/{invitation.id}/accept/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


# ═══════════════════════════════════════════════════════════════════
#  GameResultsMixin — tests approfondis
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestResultsSuccess(BaseAPIIntegrationTest):
    """GET /{room_code}/results/ — résultats réussis."""

    def get_base_url(self):
        return BASE

    def test_results_success(self, auth_client, user):
        game = GameFactory(host=user, status="finished")
        player = GamePlayerFactory(game=game, user=user, score=500)
        round_obj = GameRoundFactory(
            game=game, round_number=1, started_at=timezone.now(), ended_at=timezone.now(),
            correct_answer="Song A",
        )
        GameAnswerFactory(round=round_obj, player=player, answer="Song A", is_correct=True)
        resp = auth_client.get(f"{BASE}{game.room_code}/results/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert "game" in resp.data
        assert "rankings" in resp.data
        assert "rounds" in resp.data

    @patch("apps.games.pdf_service.generate_results_pdf")
    def test_results_pdf_success(self, mock_pdf, auth_client, user):
        mock_pdf.return_value = b"%PDF-1.4 fake content"
        game = GameFactory(host=user, status="finished")
        player = GamePlayerFactory(game=game, user=user, score=500)
        round_obj = GameRoundFactory(
            game=game, round_number=1, started_at=timezone.now(), ended_at=timezone.now(),
        )
        resp = auth_client.get(f"{BASE}{game.room_code}/results/pdf/")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"


# ═══════════════════════════════════════════════════════════════════
#  GameDiscoveryMixin — tests approfondis
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestDiscoveryPublicGames(BaseAPIIntegrationTest):
    """GET /public/ — jeux publics avec données."""

    def get_base_url(self):
        return BASE

    def test_public_games_with_data(self, auth_client, user):
        game = GameFactory(host=user, status="waiting", is_public=True)
        GamePlayerFactory(game=game, user=user)
        resp = auth_client.get(f"{BASE}public/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data["results"]

    def test_public_games_search(self, auth_client, user):
        game = GameFactory(host=user, status="waiting", is_public=True, name="UniqueGameName")
        GamePlayerFactory(game=game, user=user)
        resp = auth_client.get(f"{BASE}public/?search=UniqueGame")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_history_with_data(self, api_client, user):
        game = GameFactory(host=user, status="finished")
        resp = api_client.get(f"{BASE}history/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_leaderboard_with_data(self, api_client):
        resp = api_client.get(f"{BASE}leaderboard/")
        self.assert_status(resp, status.HTTP_200_OK)
