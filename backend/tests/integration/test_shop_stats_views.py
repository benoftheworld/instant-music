"""Tests d'intégration des vues shop et stats."""

import pytest
from rest_framework import status

from tests.base import BaseAPIIntegrationTest


@pytest.mark.django_db
class TestShopViews(BaseAPIIntegrationTest):
    """Vérifie les endpoints de la boutique."""

    def get_base_url(self):
        return "/api/shop/items/"

    def test_list_items(self, auth_client):
        """Lister les articles disponibles."""
        resp = auth_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)

    def test_list_items_unauthenticated(self, api_client):
        """Accès sans auth → 401."""
        resp = api_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)

    def test_summary(self, auth_client):
        """Résumé de la boutique."""
        resp = auth_client.get(f"{self.get_base_url()}summary/")
        self.assert_status(resp, status.HTTP_200_OK)
        assert "user_balance" in resp.data
        assert "items_count" in resp.data

    def test_purchase_missing_data(self, auth_client):
        """Achat sans données → 400."""
        resp = auth_client.post(f"{self.get_base_url()}purchase/", {}, format="json")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_purchase_nonexistent_item(self, auth_client):
        """Achat d'un article inexistant → 400."""
        import uuid
        resp = auth_client.post(
            f"{self.get_base_url()}purchase/",
            {"item_id": str(uuid.uuid4()), "quantity": 1},
            format="json",
        )
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)


@pytest.mark.django_db
class TestInventoryViews(BaseAPIIntegrationTest):
    """Vérifie les endpoints d'inventaire."""

    def get_base_url(self):
        return "/api/shop/inventory/"

    def test_list_inventory(self, auth_client):
        """Lister l'inventaire (vide)."""
        resp = auth_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_200_OK)

    def test_list_inventory_unauthenticated(self, api_client):
        resp = api_client.get(self.get_base_url())
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)

    def test_activate_missing_data(self, auth_client):
        """Activer un bonus sans données → 400."""
        resp = auth_client.post(f"{self.get_base_url()}activate/", {}, format="json")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_game_bonuses_nonexistent(self, auth_client):
        """Bonus d'une partie inexistante → 404."""
        resp = auth_client.get(f"{self.get_base_url()}game/XXXXX/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
class TestStatsViews(BaseAPIIntegrationTest):
    """Vérifie les endpoints de statistiques."""

    def get_base_url(self):
        return "/api/stats/"

    def test_user_stats(self, auth_client):
        """Statistiques de l'utilisateur connecté."""
        resp = auth_client.get(f"{self.get_base_url()}me/")
        self.assert_status(resp, status.HTTP_200_OK)
        self.assert_json_keys(resp, ["total_games_played", "total_wins"])

    def test_user_stats_unauthenticated(self, api_client):
        resp = api_client.get(f"{self.get_base_url()}me/")
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)

    def test_leaderboard(self, api_client):
        """Le classement est accessible sans auth."""
        resp = api_client.get(f"{self.get_base_url()}leaderboard/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_leaderboard_by_mode(self, api_client):
        """Classement par mode."""
        resp = api_client.get(f"{self.get_base_url()}leaderboard/classique/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_leaderboard_by_mode_invalid(self, api_client):
        """Classement par mode invalide → 400."""
        resp = api_client.get(f"{self.get_base_url()}leaderboard/invalid_mode/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_team_leaderboard(self, api_client):
        """Classement par équipe."""
        resp = api_client.get(f"{self.get_base_url()}leaderboard/teams/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_my_rank(self, auth_client):
        """Mon classement."""
        resp = auth_client.get(f"{self.get_base_url()}my-rank/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_my_rank_unauthenticated(self, api_client):
        resp = api_client.get(f"{self.get_base_url()}my-rank/")
        self.assert_status(resp, status.HTTP_401_UNAUTHORIZED)

    def test_user_public_stats(self, auth_client, user):
        """Statistiques publiques d'un utilisateur."""
        resp = auth_client.get(f"{self.get_base_url()}user/{user.id}/")
        self.assert_status(resp, status.HTTP_200_OK)

    def test_user_public_stats_not_found(self, auth_client):
        """Statistiques d'un utilisateur inexistant → 404."""
        import uuid
        resp = auth_client.get(f"{self.get_base_url()}user/{uuid.uuid4()}/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)

    def test_user_public_stats_superuser_hidden(self, auth_client, staff_user):
        """Profil public d'un superuser → 404."""
        from apps.users.models import User
        su = User.objects.create_superuser(
            username="admin_hidden", email="admin@test.com", password="pass"
        )
        resp = auth_client.get(f"{self.get_base_url()}user/{su.id}/")
        self.assert_status(resp, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
class TestPlaylistViews(BaseAPIIntegrationTest):
    """Vérifie les endpoints playlists."""

    def get_base_url(self):
        return "/api/playlists/"

    def test_search_no_query(self, auth_client):
        """Recherche sans query → 400."""
        resp = auth_client.get(f"{self.get_base_url()}search/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_youtube_search_no_query(self, auth_client):
        """Recherche YouTube sans query → 400."""
        resp = auth_client.get(f"{self.get_base_url()}youtube-songs/search/")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)

    def test_youtube_search_too_short(self, auth_client):
        """Recherche YouTube trop courte → 400."""
        resp = auth_client.get(f"{self.get_base_url()}youtube-songs/search/?query=a")
        self.assert_status(resp, status.HTTP_400_BAD_REQUEST)
