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

# ═══════════════════════════════════════════════════════════════════
#  TeamViewSet WS notification exception gaps
# ═══════════════════════════════════════════════════════════════════

TEAM_BASE = "/api/users/teams/"


@pytest.mark.django_db
class TestTeamWsNotificationExceptions(BaseAPIIntegrationTest):
    """Lines 95, 128-129, 217-218, 261-262, 439-440, 485-486 in team_viewset.py."""

    def get_base_url(self):
        return TEAM_BASE

    @patch("apps.users.views.team_viewset.async_to_sync")
    def test_join_ws_exception(self, mock_ats, auth_client2, user, user2):
        from apps.users.models import Team, TeamMember

        team = Team.objects.create(name="TestTeam", owner=user)
        TeamMember.objects.create(team=team, user=user, role="owner")
        mock_ats.return_value = MagicMock(side_effect=Exception("WS fail"))
        resp = auth_client2.post(f"{TEAM_BASE}{team.id}/join/")
        self.assert_status(resp, status.HTTP_201_CREATED)

    @patch("apps.users.views.team_viewset.async_to_sync")
    def test_approve_ws_exception(self, mock_ats, auth_client, user, user2):
        from apps.users.models import (
            Team,
            TeamJoinRequest,
            TeamJoinRequestStatus,
            TeamMember,
        )

        team = Team.objects.create(name="TestTeam", owner=user)
        TeamMember.objects.create(team=team, user=user, role="owner")
        join_req = TeamJoinRequest.objects.create(
            team=team, user=user2, status=TeamJoinRequestStatus.PENDING
        )
        mock_ats.return_value = MagicMock(side_effect=Exception("WS fail"))
        resp = auth_client.post(
            f"{TEAM_BASE}{team.id}/approve/",
            {"request_id": str(join_req.id)},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

    @patch("apps.users.views.team_viewset.async_to_sync")
    def test_reject_ws_exception(self, mock_ats, auth_client, user, user2):
        from apps.users.models import (
            Team,
            TeamJoinRequest,
            TeamJoinRequestStatus,
            TeamMember,
        )

        team = Team.objects.create(name="TestTeam", owner=user)
        TeamMember.objects.create(team=team, user=user, role="owner")
        join_req = TeamJoinRequest.objects.create(
            team=team, user=user2, status=TeamJoinRequestStatus.PENDING
        )
        mock_ats.return_value = MagicMock(side_effect=Exception("WS fail"))
        resp = auth_client.post(
            f"{TEAM_BASE}{team.id}/reject/",
            {"request_id": str(join_req.id)},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)

# ═══════════════════════════════════════════════════════════════════
#  Shop views remaining gaps
# ═══════════════════════════════════════════════════════════════════

SHOP_BASE = "/api/shop/"


@pytest.mark.django_db
class TestShopActivateBonusEdgeCases(BaseAPIIntegrationTest):
    """Lines 163-164, 171, 190-191, 212-213 in shop/views.py."""

    def get_base_url(self):
        return SHOP_BASE

    @patch("apps.shop.views.bonus_service")
    def test_activate_fifty_fifty(self, mock_bs, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        from django.utils import timezone

        round_obj = GameRoundFactory(
            game=game,
            round_number=1,
            started_at=timezone.now(),
            options=["A", "B", "C", "D"],
            correct_answer="A",
        )
        mock_bs.resolve_round_number.return_value = (1, round_obj)
        bonus_mock = MagicMock()
        mock_bs.activate_bonus.return_value = bonus_mock
        mock_bs.get_fifty_fifty_exclusions.return_value = ["B", "C"]

        resp = auth_client.post(
            f"{SHOP_BASE}inventory/activate/",
            {"bonus_type": "fifty_fifty", "room_code": game.room_code},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)
        assert "excluded_options" in resp.data

    @patch("apps.shop.views.bonus_service")
    def test_activate_steal_bonus(self, mock_bs, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user, score=50)
        from django.utils import timezone

        round_obj = GameRoundFactory(
            game=game, round_number=1, started_at=timezone.now()
        )
        mock_bs.resolve_round_number.return_value = (1, round_obj)
        bonus_mock = MagicMock()
        mock_bs.activate_bonus.return_value = bonus_mock
        mock_bs.apply_steal_bonus.return_value = 100

        resp = auth_client.post(
            f"{SHOP_BASE}inventory/activate/",
            {"bonus_type": "steal", "room_code": game.room_code},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)
        assert "stolen_points" in resp.data

    @patch("apps.shop.views.bonus_service")
    def test_activate_time_bonus(self, mock_bs, auth_client, user):
        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        from django.utils import timezone

        round_obj = GameRoundFactory(
            game=game,
            round_number=1,
            started_at=timezone.now(),
            duration=30,
        )
        mock_bs.resolve_round_number.return_value = (1, round_obj)
        bonus_mock = MagicMock()
        mock_bs.activate_bonus.return_value = bonus_mock
        mock_bs.apply_time_bonus.return_value = 45

        resp = auth_client.post(
            f"{SHOP_BASE}inventory/activate/",
            {"bonus_type": "time_bonus", "room_code": game.room_code},
            format="json",
        )
        self.assert_status(resp, status.HTTP_200_OK)
        assert resp.data.get("new_duration") == 45

    @patch("apps.shop.views.bonus_service")
    def test_activate_bonus_conflict(self, mock_bs, auth_client, user):
        from apps.shop.services import BonusAlreadyActiveError

        game = GameFactory(host=user, status="in_progress")
        GamePlayerFactory(game=game, user=user)
        from django.utils import timezone

        round_obj = GameRoundFactory(
            game=game, round_number=1, started_at=timezone.now()
        )
        mock_bs.resolve_round_number.return_value = (1, round_obj)
        mock_bs.activate_bonus.side_effect = BonusAlreadyActiveError(
            "Déjà actif"
        )

        resp = auth_client.post(
            f"{SHOP_BASE}inventory/activate/",
            {"bonus_type": "shield", "room_code": game.room_code},
            format="json",
        )
        self.assert_status(resp, status.HTTP_409_CONFLICT)