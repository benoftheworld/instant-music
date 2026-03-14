"""Tests d'intégration de l'API de login."""

from rest_framework.test import APIClient

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestAuthLogin(BaseAPIIntegrationTest):
    """Vérifie la connexion d'un utilisateur."""

    def get_base_url(self):
        return "/api/auth/login/"

    def setup_method(self):
        self.client = self.get_client()
        self.user = UserFactory(username="loginuser")
        self.user.set_password("TestP@ss123!")
        self.user.save()

    def test_login_success(self):
        data = {"username": "loginuser", "password": "TestP@ss123!"}
        resp = self.client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, 200)
        self.assert_json_keys(resp, ["user", "tokens"])

    def test_login_wrong_password(self):
        data = {"username": "loginuser", "password": "WrongPass!"}
        resp = self.client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, 401)

    def test_login_nonexistent_user(self):
        data = {"username": "nobody", "password": "TestP@ss123!"}
        resp = self.client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, 401)

    def test_login_by_email(self):
        data = {"username": self.user.email, "password": "TestP@ss123!"}
        resp = self.client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, 200)
