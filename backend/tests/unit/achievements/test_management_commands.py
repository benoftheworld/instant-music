"""Tests unitaires des commandes de management achievements."""

from io import StringIO
from unittest.mock import MagicMock, patch

from tests.base import BaseServiceUnitTest


class TestAwardRetroactiveAchievements(BaseServiceUnitTest):
    """Vérifie la commande award_retroactive_achievements."""

    def get_service_module(self):
        import apps.achievements.management.commands.award_retroactive_achievements
        return apps.achievements.management.commands.award_retroactive_achievements

    @patch("apps.achievements.management.commands.award_retroactive_achievements.GameAnswer")
    @patch("apps.achievements.management.commands.award_retroactive_achievements.GamePlayer")
    @patch("apps.achievements.management.commands.award_retroactive_achievements.User")
    @patch("apps.achievements.management.commands.award_retroactive_achievements.achievement_service")
    def test_awards_achievements(self, mock_svc, mock_user, mock_gp, mock_ga):
        from apps.achievements.management.commands.award_retroactive_achievements import Command

        mock_u = MagicMock(username="alice", total_games_played=5)
        mock_user.objects.filter.return_value = [mock_u]

        mock_player = MagicMock()
        mock_player.game.rounds.count.return_value = 5
        mock_gp.objects.filter.return_value = [mock_player]
        mock_ga.objects.filter.return_value.count.return_value = 5  # all correct = perfect

        mock_ach = MagicMock(name="Pro")
        mock_svc.check_and_award.return_value = [mock_ach]

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x
        cmd.handle()

        mock_svc.check_and_award.assert_called_once()
        output = cmd.stdout.getvalue()
        assert "alice" in output

    @patch("apps.achievements.management.commands.award_retroactive_achievements.GamePlayer")
    @patch("apps.achievements.management.commands.award_retroactive_achievements.User")
    @patch("apps.achievements.management.commands.award_retroactive_achievements.achievement_service")
    def test_no_achievements(self, mock_svc, mock_user, mock_gp):
        from apps.achievements.management.commands.award_retroactive_achievements import Command

        mock_u = MagicMock(username="bob")
        mock_user.objects.filter.return_value = [mock_u]
        mock_gp.objects.filter.return_value = []
        mock_svc.check_and_award.return_value = []

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x
        cmd.handle()

        output = cmd.stdout.getvalue()
        assert "bob" in output
        assert "no new achievements" in output


class TestSeedAchievements(BaseServiceUnitTest):
    """Vérifie la commande seed_achievements."""

    def get_service_module(self):
        import apps.achievements.management.commands.seed_achievements
        return apps.achievements.management.commands.seed_achievements

    @patch("apps.achievements.management.commands.seed_achievements.Achievement")
    def test_creates_achievements(self, mock_ach):
        from apps.achievements.management.commands.seed_achievements import Command

        # get_or_create returns (obj, created=True) for new achievements
        mock_ach.objects.get_or_create.return_value = (MagicMock(), True)

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x
        cmd.style.WARNING = lambda x: x
        cmd.handle(reset=False, force=False)

        assert mock_ach.objects.get_or_create.call_count > 0

    @patch("apps.achievements.management.commands.seed_achievements.Achievement")
    def test_skips_existing(self, mock_ach):
        from apps.achievements.management.commands.seed_achievements import Command

        # get_or_create returns (obj, created=False) for existing
        mock_ach.objects.get_or_create.return_value = (MagicMock(), False)

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x
        cmd.style.WARNING = lambda x: x
        cmd.handle(reset=False, force=False)


class TestSyncCoinsBalance(BaseServiceUnitTest):
    """Vérifie la commande sync_coins_balance."""

    def get_service_module(self):
        import apps.achievements.management.commands.sync_coins_balance
        return apps.achievements.management.commands.sync_coins_balance

    @patch("apps.achievements.management.commands.sync_coins_balance.UserInventory")
    @patch("apps.achievements.management.commands.sync_coins_balance.UserAchievement")
    @patch("apps.achievements.management.commands.sync_coins_balance.User")
    def test_syncs_balances(self, mock_user, mock_ua, mock_ui):
        from apps.achievements.management.commands.sync_coins_balance import Command

        mock_u = MagicMock(username="alice", coins_balance=100, pk=1)
        mock_user.objects.all.return_value = [mock_u]

        mock_ua.objects.filter.return_value.aggregate.return_value = {
            "total": 200
        }

        # UserInventory ORM chain: filter().annotate().aggregate()
        mock_ui.objects.filter.return_value.annotate.return_value.aggregate.return_value = {
            "total": 50
        }

        cmd = Command()
        cmd.stdout = StringIO()
        cmd.style = MagicMock()
        cmd.style.SUCCESS = lambda x: x
        cmd.style.WARNING = lambda x: x
        cmd.handle(dry_run=False)

        # expected_balance = max(0, 200 - 50) = 150 != 100 → update
        mock_user.objects.filter.assert_called_with(pk=1)

