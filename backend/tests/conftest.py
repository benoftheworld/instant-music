"""Fixtures partagées pour tous les tests (unit + integration)."""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from tests.factories import (
    UserFactory,
)

User = get_user_model()


@pytest.fixture()
def user(db):
    """Utilisateur standard de test."""
    return UserFactory(username="testuser", email="testuser@example.com")


@pytest.fixture()
def user2(db):
    """Deuxième utilisateur de test."""
    return UserFactory(username="otheruser", email="otheruser@example.com")


@pytest.fixture()
def staff_user(db):
    """Utilisateur staff de test."""
    return UserFactory(username="staffuser", email="staff@example.com", is_staff=True)


@pytest.fixture()
def api_client():
    """Client API non authentifié."""
    return APIClient()


@pytest.fixture()
def auth_client(user):
    """Client API authentifié avec l'utilisateur standard."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture()
def auth_client2(user2):
    """Client API authentifié avec le deuxième utilisateur."""
    client = APIClient()
    client.force_authenticate(user=user2)
    return client
