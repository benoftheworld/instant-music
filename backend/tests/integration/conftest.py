"""Configuration pour les tests d'intégration.

Les tests d'intégration utilisent une base de données SQLite in-memory
créée par pytest-django au début de la session et détruite à la fin.
"""

import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


def pytest_collection_modifyitems(items):
    """Ajoute marker 'integration' et 'django_db'."""
    for item in items:
        item.add_marker(pytest.mark.integration)
        item.add_marker(pytest.mark.django_db(transaction=True))
