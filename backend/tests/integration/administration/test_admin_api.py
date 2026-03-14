"""Tests d'intégration de l'API Administration."""

from tests.base import BaseAPIIntegrationTest


class TestSiteStatus(BaseAPIIntegrationTest):
    """Vérifie l'endpoint de statut du site."""

    def get_base_url(self):
        return "/api/administration/status/"

    def test_get_site_status(self):
        client = self.get_client()
        resp = client.get(self.get_base_url())
        self.assert_status(resp, 200)
        assert "maintenance" in resp.data
        assert "banner" in resp.data


class TestLegalPage(BaseAPIIntegrationTest):
    """Vérifie les pages légales."""

    def get_base_url(self):
        return "/api/administration/legal/"

    def test_legal_page_not_found(self):
        client = self.get_client()
        resp = client.get(f"{self.get_base_url()}nonexistent/")
        self.assert_status(resp, 404)

    def test_legal_page_exists(self):
        from apps.administration.models import LegalPage

        LegalPage.objects.create(
            page_type="cgu",
            title="CGU",
            content="Contenu CGU",
        )
        client = self.get_client()
        resp = client.get(f"{self.get_base_url()}cgu/")
        self.assert_status(resp, 200)
        assert resp.data["title"] == "CGU"
