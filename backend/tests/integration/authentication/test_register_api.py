"""Tests d'intégration de l'API d'authentification."""

from rest_framework.test import APIClient

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestAuthRegister(BaseAPIIntegrationTest):
    """Vérifie l'inscription d'un utilisateur."""

    def get_base_url(self):
        return "/api/auth/register/"

    def setup_method(self):
        self.client = self.get_client()

    def test_register_success(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongP@ss1!",
            "password2": "StrongP@ss1!",
            "accept_privacy_policy": True,
        }
        resp = self.client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, 201)
        self.assert_json_keys(resp, ["user", "tokens"])
        assert resp.data["user"]["username"] == "newuser"

    def test_register_password_mismatch(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongP@ss1!",
            "password2": "DifferentPass1!",
            "accept_privacy_policy": True,
        }
        resp = self.client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, 400)

    def test_register_duplicate_username(self):
        UserFactory(username="existing")
        data = {
            "username": "existing",
            "email": "unique@example.com",
            "password": "StrongP@ss1!",
            "password2": "StrongP@ss1!",
            "accept_privacy_policy": True,
        }
        resp = self.client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, 400)

    def test_register_weak_password(self):
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "123",
            "password2": "123",
            "accept_privacy_policy": True,
        }
        resp = self.client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, 400)
