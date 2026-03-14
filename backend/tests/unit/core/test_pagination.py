"""Tests unitaires du module de pagination."""

from unittest.mock import MagicMock

from apps.core.pagination import StandardResultsPagination
from tests.base import BaseUnitTest


class TestStandardResultsPagination(BaseUnitTest):
    """Vérifie la configuration de la pagination DRF."""

    def get_target_class(self):
        return StandardResultsPagination

    def test_default_page_size(self):
        assert StandardResultsPagination.page_size == 50

    def test_page_size_query_param(self):
        assert StandardResultsPagination.page_size_query_param == "page_size"

    def test_max_page_size(self):
        assert StandardResultsPagination.max_page_size == 100
