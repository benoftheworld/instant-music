"""Tests unitaires des commandes de management users."""

from io import StringIO
from unittest.mock import MagicMock, patch

from tests.base import BaseServiceUnitTest


class TestRecalculateUserStats(BaseServiceUnitTest):
    """Vérifie la commande recalculate_user_stats."""

    def get_service_module(self):
        import apps.users.management.commands.recalculate_user_stats

        return apps.users.management.commands.recalculate_user_stats

    @patch("apps.users.management.commands.recalculate_user_stats.GamePlayer")
    @patch("apps.users.management.commands.recalculate_user_stats.User")
    def test_recalculates(self, mock_user, mock_gp):
        from apps.users.management.commands.recalculate_user_stats import Command

        mock_u = MagicMock(username="alice")
        mock_user.objects.all.return_value = [mock_u]

        # Setup the chain:\n        # filter().count(), filter().filter().count(), filter().aggregate()
        mock_qs = MagicMock()
        mock_qs.count.return_value = 10
        mock_qs.filter.return_value.count.return_value = 3
        mock_qs.filter.return_value.aggregate.return_value = {
            "total": 5000,
        }
        mock_gp.objects.filter.return_value = mock_qs

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x
        cmd.style.NOTICE = lambda x: x
        cmd.handle()

        mock_u.save.assert_called_once()


class TestRecalculateTeamStats(BaseServiceUnitTest):
    """Vérifie la commande recalculate_team_stats."""

    def get_service_module(self):
        import apps.users.management.commands.recalculate_team_stats

        return apps.users.management.commands.recalculate_team_stats

    @patch("apps.users.management.commands.recalculate_team_stats.GamePlayer")
    @patch("apps.users.management.commands.recalculate_team_stats.Team")
    def test_recalculates(self, mock_team, mock_gp):
        from apps.users.management.commands.recalculate_team_stats import Command

        mock_t = MagicMock()
        mock_t.members.values_list.return_value = [1, 2]
        mock_team.objects.all.return_value = [mock_t]

        # The ORM chain returns mock queryset
        mock_qs = MagicMock()
        mock_qs.values.return_value.distinct.return_value.count.return_value = (
            10
        )
        mock_qs.filter.return_value.values.return_value.distinct.return_value.count.return_value = (  # noqa: E501
            3
        )
        mock_qs.filter.return_value.aggregate.return_value = {"s": 5000}
        mock_gp.objects.filter.return_value = mock_qs

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x
        cmd.handle()

        mock_t.save.assert_called_once()
