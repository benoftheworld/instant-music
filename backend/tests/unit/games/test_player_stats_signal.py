"""Tests unitaires de update_player_stats_on_game_finish."""

from unittest.mock import MagicMock, patch

from tests.base import BaseUnitTest


class TestUpdatePlayerStats(BaseUnitTest):
    """Vérifie le recalcul des stats joueur via le signal."""

    def get_target_class(self):
        from apps.games.signals import update_player_stats_on_game_finish
        return type(update_player_stats_on_game_finish)

    @patch("apps.games.signals.GamePlayer")
    def test_non_finished_game_skips(self, mock_gp):
        from apps.games.signals import update_player_stats_on_game_finish
        from apps.games.models import GameStatus

        instance = MagicMock()
        instance.status = GameStatus.WAITING
        update_player_stats_on_game_finish(sender=None, instance=instance)
        mock_gp.objects.filter.assert_not_called()

    @patch("django.contrib.auth.get_user_model")
    @patch("apps.games.signals.GamePlayer")
    def test_no_players_skips(self, mock_gp, mock_get_user):
        from apps.games.signals import update_player_stats_on_game_finish
        from apps.games.models import GameStatus

        instance = MagicMock()
        instance.status = GameStatus.FINISHED
        instance.players.values_list.return_value = []
        update_player_stats_on_game_finish(sender=None, instance=instance)
        mock_get_user.assert_not_called()

    @patch("django.contrib.auth.get_user_model")
    @patch("apps.games.signals.GamePlayer")
    def test_updates_user_stats(self, mock_gp, mock_get_user):
        from apps.games.signals import update_player_stats_on_game_finish
        from apps.games.models import GameStatus

        instance = MagicMock()
        instance.status = GameStatus.FINISHED
        instance.players.values_list.return_value = ["uid1"]

        stats_row = {"user_id": "uid1", "_total_games": 5, "_total_wins": 2, "_total_points": 100}
        mock_gp.objects.filter.return_value.values.return_value.annotate.return_value = [stats_row]

        User = MagicMock()
        mock_get_user.return_value = User
        user = MagicMock(id="uid1")
        User.objects.filter.return_value = [user]

        update_player_stats_on_game_finish(sender=None, instance=instance)
        assert user.total_games_played == 5
        assert user.total_wins == 2
        assert user.total_points == 100
        user.save.assert_called_once()
