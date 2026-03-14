"""Tests unitaires du liveness check."""

from unittest.mock import MagicMock

from apps.core.health import liveness_check
from tests.base import BaseUnitTest


class TestLivenessCheck(BaseUnitTest):
    """Vérifie le liveness check."""

    def get_target_class(self):
        return liveness_check

    def test_alive(self):
        request = MagicMock()
        response = liveness_check(request)
        assert response.status_code == 200
