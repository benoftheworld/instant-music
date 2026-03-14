"""Tests d'intégration de l'API de changement de mot de passe."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestChangePassword(BaseAPIIntegrationTest):
    """Vérifie le changement de mot de passe."""

    def get_base_url(self):
        return "/api/users/change_password/"

    def setup_method(self):
        self.user = UserFactory()
        self.user.set_password("OldP@ss123!")  # type: ignore[attr-defined]
        self.user.save()  # type: ignore[attr-defined]
        self.client = self.get_auth_client(self.user)

    def test_change_password_success(self):
        data = {
            "old_password": "OldP@ss123!",
            "new_password": "NewP@ss456!",
            "new_password_confirm": "NewP@ss456!",
        }
        resp = self.client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, 200)

    def test_change_password_wrong_old(self):
        data = {
            "old_password": "WrongOld!",
            "new_password": "NewP@ss456!",
            "new_password_confirm": "NewP@ss456!",
        }
        resp = self.client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, 400)

    def test_change_password_unauthenticated(self):
        client = self.get_client()
        data = {
            "old_password": "OldP@ss123!",
            "new_password": "NewP@ss456!",
            "new_password_confirm": "NewP@ss456!",
        }
        resp = client.post(self.get_base_url(), data, format="json")
        self.assert_status(resp, 401)
