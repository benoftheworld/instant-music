"""Tests unitaires de la tâche check_achievements_async."""

from unittest.mock import MagicMock, patch

from apps.achievements.tasks import check_achievements_async
from tests.base import BaseUnitTest


class TestCheckAchievementsAsync(BaseUnitTest):
    """Vérifie la tâche asynchrone de vérification des achievements."""

    def get_target_class(self):
        return check_achievements_async

    def test_calls_service(self):
        mock_user = MagicMock()

        with (
            patch("apps.users.models.User.objects") as mock_user_mgr,
            patch("apps.achievements.services.achievement_service") as mock_service,
        ):
            mock_user_mgr.get.return_value = mock_user
            check_achievements_async.__wrapped__(user_id=1)
            mock_service.check_and_award.assert_called_once()

    def test_user_not_found_returns(self):
        from apps.users.models import User

        with patch("apps.users.models.User.objects") as mock_user_mgr:
            mock_user_mgr.get.side_effect = User.DoesNotExist("not found")
            # Ne doit pas lever d'exception (return early)
            check_achievements_async.__wrapped__(user_id=999)
