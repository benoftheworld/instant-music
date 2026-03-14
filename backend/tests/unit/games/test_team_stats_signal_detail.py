"""Tests unitaires de update_team_stats_on_game_finish."""

from unittest.mock import MagicMock, patch

from tests.base import BaseUnitTest


class TestUpdateTeamStats(BaseUnitTest):
    """Vérifie le recalcul des stats d'équipe via le signal."""

    def get_target_class(self):
        from apps.games.signals import update_team_stats_on_game_finish
        return type(update_team_stats_on_game_finish)

    def test_non_finished_game_skips(self):
        from apps.games.signals import update_team_stats_on_game_finish
        from apps.games.models import GameStatus

        instance = MagicMock()
        instance.status = GameStatus.WAITING
        update_team_stats_on_game_finish(sender=None, instance=instance)

    @patch("apps.users.models.team_member.TeamMember")
    @patch("apps.users.models.Team")
    def test_no_teams_skips(self, mock_team, mock_tm):
        from apps.games.signals import update_team_stats_on_game_finish
        from apps.games.models import GameStatus

        instance = MagicMock()
        instance.status = GameStatus.FINISHED
        instance.players.values_list.return_value = ["uid1"]
        mock_tm.objects.filter.return_value.values_list.return_value = set()
        mock_team.objects.filter.assert_not_called()

    @patch("apps.games.signals.GamePlayer")
    @patch("apps.users.models.team_member.TeamMember")
    @patch("apps.users.models.Team")
    def test_updates_team_stats(self, mock_team, mock_tm, mock_gp):
        from apps.games.signals import update_team_stats_on_game_finish
        from apps.games.models import GameStatus

        instance = MagicMock()
        instance.status = GameStatus.FINISHED
        instance.players.values_list.return_value = ["uid1"]
        mock_tm.objects.filter.return_value.values_list.return_value = {"tid1"}

        team = MagicMock()
        team.members.values_list.return_value = ["uid1"]
        mock_team.objects.filter.return_value = [team]

        participations = MagicMock()
        mock_gp.objects.filter.return_value = participations
        participations.values.return_value.distinct.return_value.count.return_value = 3
        participations.filter.return_value.values.return_value.distinct.return_value.count.return_value = 1
        participations.filter.return_value.aggregate.return_value = {"s": 250}

        update_team_stats_on_game_finish(sender=None, instance=instance)
        assert team.total_games == 3
        assert team.total_wins == 1
        assert team.total_points == 250
        team.save.assert_called_once()
