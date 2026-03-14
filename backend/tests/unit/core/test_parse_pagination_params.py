"""Tests unitaires du parsing des paramètres de pagination."""

from unittest.mock import MagicMock

from apps.core.pagination import parse_pagination_params
from tests.base import BaseUnitTest


class TestParsePaginationParams(BaseUnitTest):
    """Vérifie le parsing des paramètres de pagination."""

    def get_target_class(self):
        return parse_pagination_params

    def _make_request(self, params: dict):
        request = MagicMock()
        request.query_params = params
        return request

    def test_defaults(self):
        request = self._make_request({})
        page, page_size, offset = parse_pagination_params(request)
        assert page == 1
        assert page_size == 50
        assert offset == 0

    def test_custom_page(self):
        request = self._make_request({"page": "3"})
        page, page_size, offset = parse_pagination_params(request)
        assert page == 3
        assert offset == 100

    def test_page_size_param(self):
        request = self._make_request({"page_size": "20"})
        page, page_size, offset = parse_pagination_params(request)
        assert page_size == 20

    def test_page_size_capped_at_100(self):
        request = self._make_request({"page_size": "999"})
        _, page_size, _ = parse_pagination_params(request)
        assert page_size == 100

    def test_legacy_limit_param(self):
        request = self._make_request({"limit": "25"})
        _, page_size, _ = parse_pagination_params(request)
        assert page_size == 25

    def test_page_size_takes_precedence_over_limit(self):
        request = self._make_request({"page_size": "30", "limit": "10"})
        _, page_size, _ = parse_pagination_params(request)
        assert page_size == 30

    def test_invalid_page_size_uses_default(self):
        request = self._make_request({"page_size": "abc"})
        _, page_size, _ = parse_pagination_params(request)
        assert page_size == 50

    def test_invalid_limit_uses_default(self):
        request = self._make_request({"limit": "xyz"})
        _, page_size, _ = parse_pagination_params(request)
        assert page_size == 50

    def test_page_zero_becomes_one(self):
        request = self._make_request({"page": "0"})
        page, _, offset = parse_pagination_params(request)
        assert page == 1
        assert offset == 0

    def test_negative_page_becomes_one(self):
        request = self._make_request({"page": "-5"})
        page, _, _ = parse_pagination_params(request)
        assert page == 1

    def test_custom_default_page_size(self):
        request = self._make_request({})
        _, page_size, _ = parse_pagination_params(request, default_page_size=25)
        assert page_size == 25

    def test_offset_calculation(self):
        request = self._make_request({"page": "2", "page_size": "10"})
        _, _, offset = parse_pagination_params(request)
        assert offset == 10
