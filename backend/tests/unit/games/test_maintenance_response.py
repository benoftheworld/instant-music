"""Tests unitaires de _maintenance_response_if_needed."""

from unittest.mock import MagicMock, patch

from tests.base import BaseUnitTest


class TestMaintenanceResponse(BaseUnitTest):
    """Vérifie la réponse de maintenance."""

    def get_target_class(self):
        from apps.games.views.utils import _maintenance_response_if_needed
        return type(_maintenance_response_if_needed)

    @patch("apps.administration.models.SiteConfiguration")
    def test_no_maintenance(self, mock_cfg_class):
        from apps.games.views.utils import _maintenance_response_if_needed

        mock_cfg = MagicMock(maintenance_mode=False)
        mock_cfg_class.get_solo.return_value = mock_cfg
        user = MagicMock(is_staff=False)
        result = _maintenance_response_if_needed(user)
        assert result is None

    @patch("apps.administration.models.SiteConfiguration")
    def test_maintenance_staff_passes(self, mock_cfg_class):
        from apps.games.views.utils import _maintenance_response_if_needed

        mock_cfg = MagicMock(maintenance_mode=True)
        mock_cfg_class.get_solo.return_value = mock_cfg
        user = MagicMock(is_staff=True)
        result = _maintenance_response_if_needed(user)
        assert result is None

    @patch("apps.administration.models.SiteConfiguration")
    def test_maintenance_non_staff_returns_503(self, mock_cfg_class):
        from apps.games.views.utils import _maintenance_response_if_needed

        mock_cfg = MagicMock(maintenance_mode=True)
        mock_cfg_class.get_solo.return_value = mock_cfg
        user = MagicMock(is_staff=False)
        result = _maintenance_response_if_needed(user)
        assert result is not None
        assert result.status_code == 503

    @patch("apps.administration.models.SiteConfiguration")
    def test_exception_returns_none(self, mock_cfg_class):
        from apps.games.views.utils import _maintenance_response_if_needed

        mock_cfg_class.get_solo.side_effect = Exception("DB error")
        user = MagicMock(is_staff=False)
        result = _maintenance_response_if_needed(user)
        assert result is None
