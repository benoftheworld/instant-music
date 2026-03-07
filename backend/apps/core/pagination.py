"""Utilitaires de pagination partagés.

Remplace le pattern de pagination manuelle (page/page_size/offset)
qui était dupliqué dans de nombreuses vues.
"""

from rest_framework.pagination import PageNumberPagination


class StandardResultsPagination(PageNumberPagination):
    """Pagination standard avec support du paramètre `page_size`.

    Utilisable directement sur les ViewSets ou manuellement dans les APIViews
    via `paginate_queryset()` + `get_paginated_response()`.
    """

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100


def parse_pagination_params(
    request, default_page_size: int = 50
) -> tuple[int, int, int]:
    """Parse les paramètres de pagination depuis la requête.

    Supporte `page`, `page_size` et le legacy `limit` pour la rétrocompatibilité.

    Returns:
        tuple: (page, page_size, offset)

    """
    page = max(int(request.query_params.get("page", 1)), 1)

    page_size_param = request.query_params.get("page_size", None)
    limit_param = request.query_params.get("limit", None)

    if page_size_param is not None:
        try:
            page_size = min(int(page_size_param), 100)
        except ValueError:
            page_size = default_page_size
    elif limit_param is not None:
        try:
            page_size = min(int(limit_param), 100)
        except ValueError:
            page_size = default_page_size
    else:
        page_size = default_page_size

    offset = (page - 1) * page_size
    return page, page_size, offset


def paginated_response(data: list, total_count: int, page: int, page_size: int) -> dict:
    """Construit le dictionnaire de réponse paginée."""
    return {
        "count": total_count,
        "page": page,
        "page_size": page_size,
        "results": data,
    }
