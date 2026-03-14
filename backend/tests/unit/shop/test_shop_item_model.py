"""Tests unitaires du modèle ShopItem."""

from unittest.mock import MagicMock

from django.db import models

from apps.shop.models import BonusType, ItemType, ShopItem
from tests.base import BaseModelUnitTest


class TestShopItemModel(BaseModelUnitTest):
    """Vérifie les champs et métadonnées du modèle ShopItem."""

    def get_model_class(self):
        return ShopItem

    # ── PK ──────────────────────────────────────────────────────────

    def test_pk_is_uuid(self):
        self.assert_model_has_uuid_pk()

    # ── Champs textes ───────────────────────────────────────────────

    def test_name_max_length(self):
        self.assert_field_max_length(ShopItem, "name", 100)

    def test_description_is_textfield(self):
        self.assert_field_type(ShopItem, "description", models.TextField)

    # ── item_type ───────────────────────────────────────────────────

    def test_item_type_max_length(self):
        self.assert_field_max_length(ShopItem, "item_type", 20)

    def test_item_type_choices(self):
        self.assert_field_choices(ShopItem, "item_type", ItemType.choices)

    def test_item_type_default(self):
        self.assert_field_default(ShopItem, "item_type", ItemType.BONUS)

    def test_item_type_values(self):
        assert ItemType.BONUS == "bonus"
        assert ItemType.PHYSICAL == "physical"

    # ── bonus_type ──────────────────────────────────────────────────

    def test_bonus_type_max_length(self):
        self.assert_field_max_length(ShopItem, "bonus_type", 30)

    def test_bonus_type_choices(self):
        self.assert_field_choices(ShopItem, "bonus_type", BonusType.choices)

    def test_bonus_type_null(self):
        self.assert_field_null(ShopItem, "bonus_type", True)

    def test_bonus_type_blank(self):
        self.assert_field_blank(ShopItem, "bonus_type", True)

    def test_bonus_type_values(self):
        """Vérifie les 8 types de bonus."""
        assert BonusType.DOUBLE_POINTS == "double_points"
        assert BonusType.MAX_POINTS == "max_points"
        assert BonusType.TIME_BONUS == "time_bonus"
        assert BonusType.FIFTY_FIFTY == "fifty_fifty"
        assert BonusType.STEAL == "steal"
        assert BonusType.SHIELD == "shield"
        assert BonusType.FOG == "fog"
        assert BonusType.JOKER == "joker"

    # ── Champs numériques / booléens ────────────────────────────────

    def test_cost_default(self):
        self.assert_field_default(ShopItem, "cost", 0)

    def test_is_event_only_default(self):
        self.assert_field_default(ShopItem, "is_event_only", False)

    def test_stock_null(self):
        self.assert_field_null(ShopItem, "stock", True)

    def test_stock_blank(self):
        self.assert_field_blank(ShopItem, "stock", True)

    def test_is_available_default(self):
        self.assert_field_default(ShopItem, "is_available", True)

    def test_sort_order_default(self):
        self.assert_field_default(ShopItem, "sort_order", 0)

    # ── icon ────────────────────────────────────────────────────────

    def test_icon_null(self):
        self.assert_field_null(ShopItem, "icon", True)

    def test_icon_blank(self):
        self.assert_field_blank(ShopItem, "icon", True)

    # ── Timestamps ──────────────────────────────────────────────────

    def test_created_at_auto_now_add(self):
        field = ShopItem._meta.get_field("created_at")
        assert field.auto_now_add is True

    def test_updated_at_auto_now(self):
        field = ShopItem._meta.get_field("updated_at")
        assert field.auto_now is True

    # ── Meta ────────────────────────────────────────────────────────

    def test_verbose_name(self):
        self.assert_meta_verbose_name(
            "article de la boutique", "articles de la boutique"
        )

    def test_ordering(self):
        self.assert_ordering(ShopItem, ["sort_order", "name"])

    # ── is_in_stock property ────────────────────────────────────────

    def test_is_in_stock_unlimited(self):
        """stock=None → toujours en stock."""
        item = MagicMock(spec=ShopItem)
        item.stock = None
        assert ShopItem.is_in_stock.fget(item) is True

    def test_is_in_stock_positive(self):
        """stock > 0 → en stock."""
        item = MagicMock(spec=ShopItem)
        item.stock = 5
        assert ShopItem.is_in_stock.fget(item) is True

    def test_is_in_stock_zero(self):
        """stock = 0 → hors stock."""
        item = MagicMock(spec=ShopItem)
        item.stock = 0
        assert ShopItem.is_in_stock.fget(item) is False

    # ── __str__ ─────────────────────────────────────────────────────

    def test_str_representation(self):
        item = MagicMock(spec=ShopItem)
        item.name = "Bouclier"
        item.cost = 50
        result = ShopItem.__str__(item)
        assert "Bouclier" in result
        assert "50" in result
