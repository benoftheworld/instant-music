"""Tests unitaires des signals de l'app games."""

from unittest.mock import MagicMock

from apps.games.signals import update_player_stats_on_game_finish
from tests.base import BaseUnitTest


class TestUpdatePlayerStatsSignal(BaseUnitTest):
    """Vérifie le signal de mise à jour des stats joueur."""

    def get_target_class(self):
        return update_player_stats_on_game_finish

    def test_skip_if_not_finished(self):
        """Le signal ne fait rien si la partie n'est pas terminée."""
        game = MagicMock()
        game.status = "waiting"
        # Ne doit pas lever
        update_player_stats_on_game_finish(sender=MagicMock, instance=game)

    def test_skip_if_no_players(self):
        """Le signal ne fait rien s'il n'y a pas de joueurs."""
        game = MagicMock()
        game.status = "finished"
        game.players.values_list.return_value = []
        update_player_stats_on_game_finish(sender=MagicMock, instance=game)
