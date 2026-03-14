"""Tests d'intégration de l'API d'export RGPD."""

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory


class TestUserExportData(BaseAPIIntegrationTest):
    """Vérifie l'export des données personnelles (RGPD art. 20)."""

    def get_base_url(self):
        return "/api/users/export_data/"

    def test_export_data_authenticated(self):
        user = UserFactory()
        client = self.get_auth_client(user)
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert resp["Content-Type"] == "application/json"
        assert "Content-Disposition" in resp

    def test_export_data_unauthenticated(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 401)
