"""Tests unitaires de la tâche anonymize_old_game_data."""

from unittest.mock import MagicMock, patch

from apps.administration.tasks import anonymize_old_game_data
from tests.base import BaseUnitTest


class TestAnonymizeOldGameData(BaseUnitTest):
    """Vérifie l'anonymisation des anciennes données de jeu."""

    def get_target_class(self):
        return anonymize_old_game_data

    def test_returns_counts_no_data(self):
        with (
            patch("apps.games.models.game_answer.GameAnswer.objects") as mock_answer_mgr,
            patch("apps.games.models.game.Game.objects") as mock_game_mgr,
        ):
            # Simuler aucune réponse (la boucle while s'arrête immédiatement)
            mock_filter_qs = MagicMock()
            mock_filter_qs.values_list.return_value.__getitem__ = MagicMock(return_value=[])
            mock_answer_mgr.filter.return_value = mock_filter_qs

            # Simuler aucune partie annulée
            mock_game_mgr.filter.return_value.delete.return_value = (0, {})

            result = anonymize_old_game_data.__wrapped__(retention_days=365)

        assert result["answers_deleted"] == 0
        assert result["cancelled_games_deleted"] == 0
