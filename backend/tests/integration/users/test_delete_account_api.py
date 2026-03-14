"""Tests d'intégration de l'API de suppression de compte."""

from django.contrib.auth import get_user_model

from tests.base import BaseAPIIntegrationTest
from tests.factories import UserFactory

User = get_user_model()


class TestDeleteAccount(BaseAPIIntegrationTest):
    """Vérifie la suppression RGPD du compte."""

    def get_base_url(self):
        return "/api/users/delete_account/"

    def test_delete_account_success(self):
        user = UserFactory()
        user_id = user.id
        client = self.get_auth_client(user)
        resp = client.delete(self.get_base_url())
        self.assert_status(resp, 200)
        assert not User.objects.filter(id=user_id).exists()

    def test_delete_account_unauthenticated(self):
        client = self.get_client()
        resp = client.delete(self.get_base_url())
        self.assert_status(resp, 401)
