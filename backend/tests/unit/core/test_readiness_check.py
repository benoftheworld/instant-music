"""Tests unitaires du readiness check."""

from unittest.mock import MagicMock

from apps.core.health import readiness_check
from tests.base import BaseUnitTest


class TestReadinessCheck(BaseUnitTest):
    """Vérifie le readiness check."""

    def get_target_class(self):
        return readiness_check

    def test_ready(self):
        request = MagicMock()
        response = readiness_check(request)
        assert response.status_code == 200
