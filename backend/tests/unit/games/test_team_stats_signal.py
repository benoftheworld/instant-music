"""Tests unitaires du signal update_team_stats_on_game_finish."""

from unittest.mock import MagicMock

from apps.games.signals import update_team_stats_on_game_finish
from tests.base import BaseUnitTest


class TestUpdateTeamStatsSignal(BaseUnitTest):
    """Vérifie le signal de mise à jour des stats d'équipe."""

    def get_target_class(self):
        return update_team_stats_on_game_finish

    def test_skip_if_not_finished(self):
        game = MagicMock()
        game.status = "in_progress"
        update_team_stats_on_game_finish(sender=MagicMock, instance=game)
