"""Tests d'intégration — branches manquantes vues."""

from unittest.mock import MagicMock, patch

import pytest
from rest_framework import status

from tests.base import BaseAPIIntegrationTest
from tests.factories import (
    GameFactory,
    GamePlayerFactory,
    GameRoundFactory,
    UserFactory,
)

BASE = "/api/games/"


# ═══════════════════════════════════════════════════════════════════
#  GameLobbyMixin remaining gaps
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestLobbyPatchBroadcastException(BaseAPIIntegrationTest):
    """Line 55 — broadcast_game_update exception in partial_update."""

    def get_base_url(self):
        return BASE

    @patch(
        "apps.games.views.game_lobby_mixin.broadcast_game_update",
        side_effect=Exception("WS fail"),
    )
    def test_patch_broadcast_fails_still_returns_ok(
        self, mock_bc, auth_client, user
    ):
        game = GameFactory(host=user, status="waiting")
        GamePlayerFactory(game=game, user=user)
        resp = auth_client.patch(
            f"{BASE}{game.room_code}/",
            {"max_players": 6},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)


@pytest.mark.django_db
class TestLobbyJoinBroadcast(BaseAPIIntegrationTest):
    """Lines 73-74 — join broadcasts player_join event."""

    def get_base_url(self):
        return BASE

    @patch("apps.games.views.game_lobby_mixin.broadcast_player_join")
    def test_join_calls_broadcast(self, mock_bc, auth_client2, user, user2):
        game = GameFactory(host=user, status="waiting", max_players=4)
        GamePlayerFactory(game=game, user=user)
        resp = auth_client2.post(f"{BASE}{game.room_code}/join/")
        self.assert_status(resp, status.HTTP_201_CREATED)
        mock_bc.assert_called_once()


@pytest.mark.django_db
class TestLobbyLeaveHost(BaseAPIIntegrationTest):
    """Line 81 — host leave cancels game and broadcasts player_leave."""

    def get_base_url(self):
        return BASE

    @patch("apps.games.views.game_lobby_mixin.broadcast_player_leave")
    def test_host_leave_cancels_game(self, mock_bc, auth_client, user):
        game = GameFactory(host=user, status="waiting")
        GamePlayerFactory(game=game, user=user)
        resp = auth_client.post(f"{BASE}{game.room_code}/leave/")
        self.assert_status(resp, status.HTTP_200_OK)
        game.refresh_from_db()  # type: ignore[attr-defined]
        assert game.status == "cancelled"
        mock_bc.assert_called_once()

    @patch("apps.games.views.game_lobby_mixin.broadcast_player_leave")
    def test_nonhost_leave_broadcasts(
        self, mock_bc, auth_client2, user, user2
    ):
        game = GameFactory(host=user, status="waiting")
        GamePlayerFactory(game=game, user=user)
        GamePlayerFactory(game=game, user=user2)
        resp = auth_client2.post(f"{BASE}{game.room_code}/leave/")
        self.assert_status(resp, status.HTTP_200_OK)
        mock_bc.assert_called_once()


@pytest.mark.django_db
class TestLobbyStartPartyMode(BaseAPIIntegrationTest):
    """Lines 187-189 — party mode checks non-host player count."""

    def get_base_url(self):
        return BASE

    def test_party_mode_no_players_except_host(self, auth_client, user):
        game = GameFactory(
            host=user,
            status="waiting",
            is_party_mode=True,
            is_online=True,
            playlist_id="123",
        )
        GamePlayerFactory(game=game, user=user)
        resp = auth_client.post(f"{BASE}{game.room_code}/start/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)
        assert "présentateur" in resp.data.get("error", "")

    @patch("apps.games.views.game_lobby_mixin.game_service")
    @patch("apps.games.views.game_lobby_mixin.broadcast_game_start")
    @patch("apps.games.views.game_lobby_mixin.broadcast_round_start")
    def test_party_mode_with_players_starts(
        self, mock_brs, mock_bgs, mock_gs, auth_client, user
    ):
        game = GameFactory(
            host=user,
            status="waiting",
            is_party_mode=True,
            is_online=True,
            playlist_id="123",
        )
        GamePlayerFactory(game=game, user=user)
        other = UserFactory()
        GamePlayerFactory(game=game, user=other)
        round_obj = GameRoundFactory(game=game, round_number=1)
        mock_gs.start_game.return_value = (game, [round_obj])
        resp = auth_client.post(f"{BASE}{game.room_code}/start/")
        self.assert_status(resp, status.HTTP_200_OK)


@pytest.mark.django_db
class TestLobbyStartBroadcasts(BaseAPIIntegrationTest):
    """Lines 220-225 — broadcast game_start then round_start."""

    def get_base_url(self):
        return BASE

    @patch("apps.games.views.game_lobby_mixin.broadcast_round_start")
    @patch("apps.games.views.game_lobby_mixin.broadcast_game_start")
    @patch("apps.games.views.game_lobby_mixin.game_service")
    def test_start_broadcasts_both(
        self, mock_gs, mock_bgs, mock_brs, auth_client, user
    ):
        game = GameFactory(
            host=user, status="waiting", is_online=False, playlist_id="123"
        )
        GamePlayerFactory(game=game, user=user)
        round_obj = GameRoundFactory(game=game, round_number=1)
        mock_gs.start_game.return_value = (game, [round_obj])
        resp = auth_client.post(f"{BASE}{game.room_code}/start/")
        self.assert_status(resp, status.HTTP_200_OK)
        mock_bgs.assert_called_once()
        mock_brs.assert_called_once()


# ═══════════════════════════════════════════════════════════════════
#  GameRoundMixin remaining gaps (lines 94, 170)
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.django_db
class TestRoundEndNoActiveRound(BaseAPIIntegrationTest):
    """Line 94 — end_round when no active (started, not ended) round exists."""

    def get_base_url(self):
        return BASE

    def test_end_round_no_active_round(self, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        resp = auth_client.post(f"{BASE}{game.room_code}/end-round/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)