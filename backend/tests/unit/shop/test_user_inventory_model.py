"""Tests unitaires du modèle UserInventory."""

from unittest.mock import MagicMock

from apps.shop.models import UserInventory
from tests.base import BaseModelUnitTest


class TestUserInventoryModel(BaseModelUnitTest):
    """Vérifie les champs et métadonnées du modèle UserInventory."""

    def get_model_class(self):
        return UserInventory

    # ── PK ──────────────────────────────────────────────────────────

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champs ──────────────────────────────────────────────────────

    def test_quantity_default(self):
        self.assert_field_default(UserInventory, "quantity", 1)

    def test_purchased_at_auto_now_add(self):
        field = UserInventory._meta.get_field("purchased_at")
        assert field.auto_now_add is True

    # ── FK ──────────────────────────────────────────────────────────

    def test_user_cascade(self):
        field = UserInventory._meta.get_field("user")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    def test_item_cascade(self):
        field = UserInventory._meta.get_field("item")
        assert field.remote_field.on_delete.__name__ == "CASCADE"

    # ── Meta ────────────────────────────────────────────────────────

    def test_unique_together(self):
        self.assert_unique_together(UserInventory, ["user", "item"])

    def test_verbose_name(self):
        self.assert_meta_verbose_name(
            "inventaire utilisateur", "inventaires utilisateurs"
        )

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        mock_user = MagicMock()
        mock_user.username = "alice"
        mock_item = MagicMock()
        mock_item.name = "Bouclier"
        inv = MagicMock(spec=UserInventory)
        inv.user = mock_user
        inv.item = mock_item
        inv.quantity = 3
        result = UserInventory.__str__(inv)
        assert "alice" in result
        assert "Bouclier" in result
