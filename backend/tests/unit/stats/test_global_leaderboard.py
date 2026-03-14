"""Tests unitaires de get_global_leaderboard."""

from unittest.mock import MagicMock, patch

from tests.base import BaseUnitTest


class TestGetGlobalLeaderboard(BaseUnitTest):
    """Vérifie la pagination et filtres du leaderboard global."""

    def get_target_class(self):
        from apps.stats.services import get_global_leaderboard

        return type(get_global_leaderboard)

    @patch("apps.stats.services._build_leaderboard_entry")
    @patch("apps.stats.services.User")
    def test_returns_entries_and_count(self, mock_user, mock_build):
        from apps.stats.services import get_global_leaderboard

        u1 = MagicMock()
        u2 = MagicMock()
        qs = MagicMock()
        mock_user.objects.filter.return_value.exclude.return_value.prefetch_related.return_value.order_by.return_value = (  # noqa: E501
            qs
        )
        qs.count.return_value = 2
        qs.__getitem__ = MagicMock(return_value=[u1, u2])
        mock_build.side_effect = lambda idx, u: {"rank": idx, "user": u}
        data, total = get_global_leaderboard(0, 10)
        assert total == 2
        assert len(data) == 2

    @patch("apps.stats.services._build_leaderboard_entry")
    @patch("apps.stats.services.User")
    def test_empty_leaderboard(self, mock_user, mock_build):
        from apps.stats.services import get_global_leaderboard

        qs = MagicMock()
        mock_user.objects.filter.return_value.exclude.return_value.prefetch_related.return_value.order_by.return_value = (  # noqa: E501
            qs
        )
        qs.count.return_value = 0
        qs.__getitem__ = MagicMock(return_value=[])
        data, total = get_global_leaderboard(0, 10)
        assert total == 0
        assert data == []
