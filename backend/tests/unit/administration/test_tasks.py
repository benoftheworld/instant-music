"""Tests unitaires des tâches Celery d'administration."""

from unittest.mock import MagicMock, patch

from apps.administration.tasks import purge_expired_invitations
from tests.base import BaseUnitTest


class TestPurgeExpiredInvitations(BaseUnitTest):
    """Vérifie la purge des invitations expirées."""

    def get_target_class(self):
        return purge_expired_invitations

    def test_deletes_expired(self):
        mock_qs = MagicMock()
        mock_qs.delete.return_value = (5, {})

        with patch(
            "apps.games.models.game_invitation.GameInvitation.objects"
        ) as mock_objects:
            mock_objects.filter.return_value = mock_qs
            result = purge_expired_invitations.__wrapped__()

        assert result == 5

    def test_retry_on_exception(self):
        with (
            patch(
                "apps.games.models.game_invitation.GameInvitation.objects"
            ) as mock_objects,
            patch.object(
                purge_expired_invitations, "retry", side_effect=Exception("retrying")
            ) as mock_retry,
        ):
            mock_objects.filter.side_effect = Exception("DB error")
            try:
                purge_expired_invitations.__wrapped__()
            except Exception:
                pass

            mock_retry.assert_called_once()
