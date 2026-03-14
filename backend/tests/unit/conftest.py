"""Configuration pour les tests unitaires.

Les tests unitaires n'utilisent PAS la base de données.
Tout est mocké — aucune dépendance externe.
"""

import pytest


def pytest_collection_modifyitems(items):
    """Ajouter automatiquement le marker 'unit' à tous les tests de ce dossier."""
    for item in items:
        item.add_marker(pytest.mark.unit)
