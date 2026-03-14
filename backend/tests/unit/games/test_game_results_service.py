"""Tests du game_results_service."""

from unittest.mock import MagicMock, patch

from tests.base import BaseServiceUnitTest


class TestBuildRankings(BaseServiceUnitTest):
    """Vérifie la construction du classement."""

    def get_service_module(self):
        import apps.games.game_results_service
        return apps.games.game_results_service

    def test_builds_rankings(self):
        from apps.games.game_results_service import build_rankings

        mock_user = MagicMock()
        mock_user.id = "uid1"
        mock_user.username = "alice"
        mock_user.avatar = None
        mock_user.team_memberships.first.return_value = None

        mock_player = MagicMock()
        mock_player.user = mock_user
        mock_player.score = 200
        mock_player.rank = 1

        mock_game = MagicMock()
        mock_game.is_party_mode = False
        mock_game.competitive_players.return_value.order_by.return_value.select_related.return_value.prefetch_related.return_value = [
            mock_player
        ]

        result = build_rankings(mock_game)
        assert len(result) == 1
        assert result[0]["username"] == "alice"
        assert result[0]["rank"] == 1
        assert result[0]["team_name"] is None

    def test_party_mode_excludes_host(self):
        from apps.games.game_results_service import build_rankings

        mock_game = MagicMock()
        mock_game.is_party_mode = True
        mock_game.host = MagicMock()
        chain = (
            mock_game.competitive_players.return_value.order_by.return_value.select_related.return_value.prefetch_related.return_value
        )
        chain.exclude.return_value = []

        result = build_rankings(mock_game)
        assert result == []

    def test_rankings_with_team(self):
        from apps.games.game_results_service import build_rankings

        mock_team = MagicMock()
        mock_team.name = "Team Alpha"

        mock_tm = MagicMock()
        mock_tm.team = mock_team

        mock_user = MagicMock()
        mock_user.id = "uid1"
        mock_user.username = "bob"
        mock_user.avatar = None
        mock_user.team_memberships.first.return_value = mock_tm

        mock_player = MagicMock()
        mock_player.user = mock_user
        mock_player.score = 150
        mock_player.rank = 2

        mock_game = MagicMock()
        mock_game.is_party_mode = False
        mock_game.competitive_players.return_value.order_by.return_value.select_related.return_value.prefetch_related.return_value = [
            mock_player
        ]

        result = build_rankings(mock_game)
        assert result[0]["team_name"] == "Team Alpha"


class TestBuildRoundsDetail(BaseServiceUnitTest):
    """Vérifie la construction du détail des rounds."""

    def get_service_module(self):
        import apps.games.game_results_service
        return apps.games.game_results_service

    @patch("apps.shop.models.GameBonus")
    @patch("apps.games.game_results_service.GameRound")
    def test_empty_game(self, mock_round_cls, mock_bonus_cls):
        from apps.games.game_results_service import build_rounds_detail

        mock_bonus_cls.objects.filter.return_value.select_related.return_value.order_by.return_value = (
            []
        )
        mock_round_cls.objects.filter.return_value.prefetch_related.return_value.order_by.return_value = (
            []
        )

        game = MagicMock()
        rounds_detail, streaks = build_rounds_detail(game)
        assert rounds_detail == []
        assert streaks == {}
