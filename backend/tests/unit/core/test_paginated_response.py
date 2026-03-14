"""Tests unitaires de la construction de réponse paginée."""

from apps.core.pagination import paginated_response
from tests.base import BaseUnitTest


class TestPaginatedResponse(BaseUnitTest):
    """Vérifie la construction de la réponse paginée."""

    def get_target_class(self):
        return paginated_response

    def test_structure(self):
        result = paginated_response(
            data=[{"id": 1}], total_count=100, page=1, page_size=50
        )
        assert result["count"] == 100
        assert result["page"] == 1
        assert result["page_size"] == 50
        assert result["results"] == [{"id": 1}]

    def test_empty_data(self):
        result = paginated_response(data=[], total_count=0, page=1, page_size=50)
        assert result["count"] == 0
        assert result["results"] == []
