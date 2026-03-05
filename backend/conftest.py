"""Fixtures partagées pour les tests backend.
"""

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture()
def user(db):
    """Utilisateur standard de test."""
    return User.objects.create_user(
        username="testuser",
        email="testuser@example.com",
        password="Testpass123!",
    )


@pytest.fixture()
def user2(db):
    """Deuxième utilisateur de test."""
    return User.objects.create_user(
        username="otheruser",
        email="otheruser@example.com",
        password="Testpass123!",
    )


@pytest.fixture()
def staff_user(db):
    """Utilisateur staff de test."""
    return User.objects.create_user(
        username="staffuser",
        email="staff@example.com",
        password="Testpass123!",
        is_staff=True,
    )


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
