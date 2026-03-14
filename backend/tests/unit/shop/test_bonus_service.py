"""Tests unitaires du BonusService."""

from unittest.mock import MagicMock, patch

import pytest

from tests.base import BaseServiceUnitTest


class TestBonusServiceResolveRound(BaseServiceUnitTest):
    """Vérifie resolve_round_number."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import BonusService

        return BonusService()

    def test_fog_requires_active_round(self):
        from apps.shop.services import BonusActivationError

        svc = self._make_svc()
        game = MagicMock()
        game.rounds.filter.return_value.first.return_value = None
        with pytest.raises(BonusActivationError):
            svc.resolve_round_number(game, "fog")

    def test_fog_returns_next_round(self):
        svc = self._make_svc()
        game = MagicMock()
        current = MagicMock(round_number=3)
        game.rounds.filter.return_value.first.return_value = current
        rn, cr = svc.resolve_round_number(game, "fog")
        assert rn == 4
        assert cr == current

    def test_joker_requires_active_round(self):
        from apps.shop.services import BonusActivationError

        svc = self._make_svc()
        game = MagicMock()
        game.rounds.filter.return_value.first.return_value = None
        with pytest.raises(BonusActivationError):
            svc.resolve_round_number(game, "joker")

    def test_normal_bonus(self):
        svc = self._make_svc()
        game = MagicMock()
        current = MagicMock(round_number=2)
        game.rounds.filter.return_value.first.return_value = current
        rn, cr = svc.resolve_round_number(game, "double_points")
        assert rn == 2
        assert cr == current


class TestBonusServiceActivate(BaseServiceUnitTest):
    """Vérifie activate_bonus."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import BonusService

        return BonusService()

    @patch("apps.shop.services.GameBonus")
    @patch("apps.shop.services.UserInventory")
    @patch("apps.shop.services.ShopItem")
    @patch("apps.games.models.GamePlayer")
    def test_activate_success(self, mock_gp, mock_si, mock_ui, mock_gb):
        svc = self._make_svc()
        player = MagicMock()
        mock_gp.objects.get.return_value = player
        item = MagicMock()
        mock_si.objects.get.return_value = item
        inv = MagicMock(quantity=5)
        mock_ui.objects.select_for_update.return_value.get.return_value = inv
        mock_gb.objects.create.return_value = MagicMock()
        mock_gb.objects.filter.return_value.exists.return_value = False

        svc.activate_bonus.__wrapped__(
            svc, MagicMock(), MagicMock(), "double_points", round_number=1
        )
        assert inv.quantity == 4

    @patch("apps.games.models.GamePlayer")
    def test_activate_not_in_game(self, mock_gp):
        from django.core.exceptions import ObjectDoesNotExist

        svc = self._make_svc()
        mock_gp.DoesNotExist = ObjectDoesNotExist
        mock_gp.objects.get.side_effect = ObjectDoesNotExist
        with pytest.raises(ValueError):
            svc.activate_bonus.__wrapped__(
                svc, MagicMock(), MagicMock(), "double_points"
            )


class TestBonusServiceApplyScore(BaseServiceUnitTest):
    """Vérifie apply_score_bonuses."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import BonusService

        return BonusService()

    def test_incorrect_answer_no_bonus(self):
        svc = self._make_svc()
        points, bonuses = svc.apply_score_bonuses(
            player=MagicMock(),
            round_number=1,
            base_points=50,
            is_correct=False,
            game=MagicMock(),
        )
        assert points == 50
        assert bonuses == []

    @patch("apps.shop.services.GameBonus")
    def test_double_points(self, mock_gb):
        from apps.shop.models import BonusType

        svc = self._make_svc()
        bonus = MagicMock(bonus_type=BonusType.DOUBLE_POINTS)
        mock_gb.objects.filter.return_value.select_for_update.return_value = [bonus]
        points, bonuses = svc.apply_score_bonuses(
            player=MagicMock(),
            round_number=1,
            base_points=50,
            is_correct=True,
            game=MagicMock(),
        )
        assert points == 100
        assert BonusType.DOUBLE_POINTS in bonuses

    @patch("apps.shop.services.GameBonus")
    def test_max_points(self, mock_gb):
        from apps.shop.models import BonusType

        svc = self._make_svc()
        bonus = MagicMock(bonus_type=BonusType.MAX_POINTS)
        mock_gb.objects.filter.return_value.select_for_update.return_value = [bonus]
        points, bonuses = svc.apply_score_bonuses(
            player=MagicMock(),
            round_number=1,
            base_points=20,
            is_correct=True,
            game=MagicMock(),
        )
        assert points >= 20
        assert BonusType.MAX_POINTS in bonuses


class TestBonusServiceFiftyFifty(BaseServiceUnitTest):
    """Vérifie get_fifty_fifty_exclusions."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import BonusService

        return BonusService()

    @patch("apps.shop.services.GameBonus")
    def test_returns_two_wrong_answers(self, mock_gb):
        svc = self._make_svc()
        bonus = MagicMock()
        mock_gb.objects.filter.return_value.exists.return_value = True
        mock_gb.objects.filter.return_value.__iter__ = lambda s: iter([bonus])
        options = ["Song1", "Song2", "Song3", "Song4"]
        excluded = svc.get_fifty_fifty_exclusions(
            player=MagicMock(),
            round_number=1,
            options=options,
            correct_answer="Song1",
        )
        assert len(excluded) == 2
        assert "Song1" not in excluded

    @patch("apps.shop.services.GameBonus")
    def test_no_bonus_returns_empty(self, mock_gb):
        svc = self._make_svc()
        mock_gb.objects.filter.return_value.exists.return_value = False
        result = svc.get_fifty_fifty_exclusions(
            player=MagicMock(),
            round_number=1,
            options=["a", "b", "c"],
            correct_answer="a",
        )
        assert result == []


class TestBonusServiceSteal(BaseServiceUnitTest):
    """Vérifie apply_steal_bonus."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import BonusService

        return BonusService()

    @patch("apps.shop.services.GameBonus")
    @patch("apps.games.models.GamePlayer")
    def test_steal_success(self, mock_gp, mock_gb):
        svc = self._make_svc()
        bonus = MagicMock()
        mock_gb.objects.filter.return_value.exists.return_value = True
        mock_gb.objects.filter.return_value.__iter__ = lambda s: iter([bonus])

        leader = MagicMock(score=200)
        mock_gp.objects.filter.return_value.exclude.return_value.order_by.return_value.first.return_value = (  # noqa: E501
            leader
        )

        # No shield
        mock_gb.objects.filter.side_effect = None
        # Reset for different calls
        call_count = [0]

        def side_effect_filter(**kwargs):
            call_count[0] += 1
            result = MagicMock()
            if kwargs.get("bonus_type") == "shield":
                result.exists.return_value = False
            else:
                result.exists.return_value = True
                result.__iter__ = lambda s: iter([bonus])
            return result

        mock_gb.objects.filter = side_effect_filter

        player = MagicMock(score=50)
        stolen = svc.apply_steal_bonus(player, MagicMock(), round_number=1)
        assert stolen == 100

    @patch("apps.shop.services.GameBonus")
    def test_steal_no_bonus(self, mock_gb):
        svc = self._make_svc()
        mock_gb.objects.filter.return_value.exists.return_value = False
        result = svc.apply_steal_bonus(MagicMock(), MagicMock(), round_number=1)
        assert result == 0


class TestBonusServiceTimeBonus(BaseServiceUnitTest):
    """Vérifie apply_time_bonus."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import BonusService

        return BonusService()

    @patch("apps.shop.services.GameBonus")
    @patch("apps.games.models.GamePlayer")
    def test_apply_time_bonus(self, mock_gp, mock_gb):
        svc = self._make_svc()
        mock_gp.objects.get.return_value = MagicMock()
        bonus = MagicMock()
        mock_gb.objects.filter.return_value.exists.return_value = True
        mock_gb.objects.filter.return_value.__iter__ = lambda s: iter([bonus])
        round_obj = MagicMock(duration=30, round_number=1, game=MagicMock())
        result = svc.apply_time_bonus(player=MagicMock(), round_obj=round_obj)
        assert result == 45  # 30 + 15

    @patch("apps.shop.services.GameBonus")
    @patch("apps.games.models.GamePlayer")
    def test_no_time_bonus(self, mock_gp, mock_gb):
        svc = self._make_svc()
        mock_gp.objects.get.return_value = MagicMock()
        mock_gb.objects.filter.return_value.exists.return_value = False
        round_obj = MagicMock(duration=30, round_number=1, game=MagicMock())
        result = svc.apply_time_bonus(player=MagicMock(), round_obj=round_obj)
        assert result == 0

    @patch("apps.shop.services.GameBonus")
    @patch("apps.games.models.GamePlayer")
    def test_player_not_in_game(self, mock_gp, mock_gb):
        from django.core.exceptions import ObjectDoesNotExist

        svc = self._make_svc()
        mock_gp.DoesNotExist = ObjectDoesNotExist
        mock_gp.objects.get.side_effect = ObjectDoesNotExist
        result = svc.apply_time_bonus(player=MagicMock(), round_obj=MagicMock())
        assert result == 0


class TestBonusServiceConsume(BaseServiceUnitTest):
    """Vérifie consume_bonus."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import BonusService

        return BonusService()

    def test_consume_marks_used(self):
        svc = self._make_svc()
        bonus = MagicMock()
        svc.consume_bonus(bonus)
        assert bonus.is_used is True
        bonus.save.assert_called_once()

    @patch("apps.shop.services.GameBonus")
    def test_get_active_bonuses(self, mock_gb):
        svc = self._make_svc()
        mock_gb.objects.filter.return_value = [MagicMock()]
        result = svc.get_active_bonuses_for_player(MagicMock(), round_number=1)
        assert len(result) == 1


class TestShopServicePurchase(BaseServiceUnitTest):
    """Vérifie shop_service.purchase."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import ShopService

        return ShopService()

    @patch("apps.shop.services.UserInventory")
    @patch("apps.shop.services.ShopItem")
    def test_purchase_success(self, mock_si, mock_ui):
        svc = self._make_svc()
        item = MagicMock(cost=50, is_event_only=False, stock=None)
        mock_si.objects.select_for_update.return_value.get.return_value = item
        inventory = MagicMock(quantity=1)
        mock_ui.objects.get_or_create.return_value = (inventory, True)
        user = MagicMock(id=1, coins_balance=100)

        with patch("apps.users.coin_service.deduct_coins"):
            result = svc.purchase.__wrapped__(svc, user, item_id="1", quantity=1)
        assert result == inventory

    @patch("apps.shop.services.ShopItem")
    def test_purchase_not_found(self, mock_si):
        from apps.shop.models import ShopItem as _SI
        from apps.shop.services import ItemNotAvailableError

        svc = self._make_svc()
        mock_si.DoesNotExist = _SI.DoesNotExist
        mock_si.objects.select_for_update.return_value.get.side_effect = (
            _SI.DoesNotExist
        )
        with pytest.raises(ItemNotAvailableError):
            svc.purchase.__wrapped__(svc, MagicMock(), item_id="1")

    @patch("apps.shop.services.ShopItem")
    def test_purchase_event_only_free(self, mock_si):
        from apps.shop.services import ItemNotAvailableError

        svc = self._make_svc()
        item = MagicMock(cost=0, is_event_only=True)
        mock_si.objects.select_for_update.return_value.get.return_value = item
        with pytest.raises(ItemNotAvailableError):
            svc.purchase.__wrapped__(svc, MagicMock(), item_id="1")

    @patch("apps.shop.services.ShopItem")
    def test_purchase_insufficient_stock(self, mock_si):
        from apps.shop.services import ItemNotAvailableError

        svc = self._make_svc()
        item = MagicMock(cost=10, is_event_only=False, stock=0)
        mock_si.objects.select_for_update.return_value.get.return_value = item
        with pytest.raises(ItemNotAvailableError):
            svc.purchase.__wrapped__(svc, MagicMock(), item_id="1", quantity=1)


class TestShopServicePurchaseStock(BaseServiceUnitTest):
    """Vérifie la mise à jour du stock et de l'inventaire existant."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import ShopService

        return ShopService()

    @patch("apps.shop.services.UserInventory")
    @patch("apps.shop.services.ShopItem")
    def test_purchase_decrements_finite_stock(self, mock_si, mock_ui):
        svc = self._make_svc()
        item = MagicMock(cost=10, is_event_only=False, stock=5, name="TestItem")
        mock_si.objects.select_for_update.return_value.get.return_value = item
        inventory = MagicMock(quantity=1)
        mock_ui.objects.get_or_create.return_value = (inventory, True)
        user = MagicMock(id=1, coins_balance=100)

        with patch("apps.users.coin_service.deduct_coins"):
            svc.purchase.__wrapped__(svc, user, item_id="1", quantity=2)

        assert item.stock == 3
        item.save.assert_called_once_with(update_fields=["stock"])

    @patch("apps.shop.services.UserInventory")
    @patch("apps.shop.services.ShopItem")
    def test_purchase_existing_inventory_increases_quantity(self, mock_si, mock_ui):
        svc = self._make_svc()
        item = MagicMock(cost=10, is_event_only=False, stock=None, name="TestItem")
        mock_si.objects.select_for_update.return_value.get.return_value = item
        inventory = MagicMock(quantity=3)
        # created=False => already exists in inventory
        mock_ui.objects.get_or_create.return_value = (inventory, False)
        user = MagicMock(id=1, coins_balance=100)

        with patch("apps.users.coin_service.deduct_coins"):
            svc.purchase.__wrapped__(svc, user, item_id="1", quantity=2)

        assert inventory.quantity == 5
        inventory.save.assert_called_once_with(update_fields=["quantity"])


class TestShopServiceTotalCoins(BaseServiceUnitTest):
    """Vérifie get_total_coins_available."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import ShopService

        return ShopService()

    @patch("apps.achievements.models.Achievement")
    def test_returns_total_or_zero(self, mock_achievement):
        svc = self._make_svc()
        mock_achievement.objects.aggregate.return_value = {"total": 500}
        result = svc.get_total_coins_available()
        assert result == 500

    @patch("apps.achievements.models.Achievement")
    def test_returns_zero_when_none(self, mock_achievement):
        svc = self._make_svc()
        mock_achievement.objects.aggregate.return_value = {"total": None}
        result = svc.get_total_coins_available()
        assert result == 0


class TestBonusServiceActivateBonus(BaseServiceUnitTest):
    """Vérifie activate_bonus du BonusService."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import BonusService

        return BonusService()

    @patch("apps.shop.services.GameBonus")
    @patch("apps.shop.services.UserInventory")
    @patch("apps.shop.services.ShopItem")
    @patch("apps.games.models.GamePlayer")
    def test_activate_success(self, mock_gp, mock_si, mock_ui, mock_gb):
        svc = self._make_svc()
        player = MagicMock()
        mock_gp.objects.get.return_value = player
        item = MagicMock()
        mock_si.objects.get.return_value = item
        inventory = MagicMock(quantity=3)
        mock_ui.objects.select_for_update.return_value.get.return_value = inventory
        bonus = MagicMock()
        mock_gb.objects.create.return_value = bonus

        result = svc.activate_bonus.__wrapped__(
            svc,
            user=MagicMock(),
            game=MagicMock(),
            bonus_type="fifty_fifty",
            round_number=1,
        )
        assert result == bonus
        assert inventory.quantity == 2
        inventory.save.assert_called_once_with(update_fields=["quantity"])

    @patch("apps.games.models.GamePlayer")
    def test_activate_player_not_in_game(self, mock_gp):
        from django.core.exceptions import ObjectDoesNotExist

        svc = self._make_svc()
        mock_gp.DoesNotExist = ObjectDoesNotExist
        mock_gp.objects.get.side_effect = ObjectDoesNotExist
        with pytest.raises(ValueError, match="ne participez pas"):
            svc.activate_bonus.__wrapped__(
                svc, user=MagicMock(), game=MagicMock(), bonus_type="steal"
            )

    @patch("apps.shop.services.ShopItem")
    @patch("apps.games.models.GamePlayer")
    def test_activate_item_not_found(self, mock_gp, mock_si):
        from apps.shop.models import ShopItem as _SI
        from apps.shop.services import ItemNotAvailableError

        svc = self._make_svc()
        mock_gp.objects.get.return_value = MagicMock()
        mock_si.DoesNotExist = _SI.DoesNotExist
        mock_si.objects.get.side_effect = _SI.DoesNotExist
        with pytest.raises(ItemNotAvailableError):
            svc.activate_bonus.__wrapped__(
                svc, user=MagicMock(), game=MagicMock(), bonus_type="steal"
            )

    @patch("apps.shop.services.GameBonus")
    @patch("apps.shop.services.UserInventory")
    @patch("apps.shop.services.ShopItem")
    @patch("apps.games.models.GamePlayer")
    def test_activate_unique_bonus_already_active(
        self, mock_gp, mock_si, mock_ui, mock_gb
    ):
        from apps.shop.services import BonusAlreadyActiveError

        svc = self._make_svc()
        mock_gp.objects.get.return_value = MagicMock()
        mock_si.objects.get.return_value = MagicMock()
        mock_ui.objects.select_for_update.return_value.get.return_value = MagicMock(
            quantity=1
        )
        mock_gb.objects.filter.return_value.exists.return_value = True

        with pytest.raises(BonusAlreadyActiveError):
            svc.activate_bonus.__wrapped__(
                svc, user=MagicMock(), game=MagicMock(), bonus_type="shield"
            )


class TestBonusServiceStealShield(BaseServiceUnitTest):
    """Vérifie que le bouclier bloque le vol."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import BonusService

        return BonusService()

    @patch("apps.shop.services.GameBonus")
    @patch("apps.games.models.GamePlayer")
    def test_steal_blocked_by_shield(self, mock_gp, mock_gb):
        svc = self._make_svc()
        bonus = MagicMock()

        leader = MagicMock(score=200)
        mock_gp.objects.filter.return_value.exclude.return_value.order_by.return_value.first.return_value = (  # noqa: E501
            leader
        )

        call_count = [0]

        def side_effect_filter(**kwargs):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                # First call: check steal bonus exists
                result.exists.return_value = True
                result.__iter__ = lambda s: iter([bonus])
            elif call_count[0] == 2:
                # Second call: check leader has shield
                result.exists.return_value = True
            else:
                result.exists.return_value = False
            return result

        mock_gb.objects.filter = side_effect_filter

        player = MagicMock(score=50)
        stolen = svc.apply_steal_bonus(player, MagicMock(), round_number=1)
        assert stolen == 0


class TestShopServiceInventory(BaseServiceUnitTest):
    """Vérifie get_user_inventory."""

    def get_service_module(self):
        from apps.shop import services

        return services

    def _make_svc(self):
        from apps.shop.services import ShopService

        return ShopService()

    @patch("apps.shop.services.UserInventory")
    def test_get_inventory(self, mock_ui):
        svc = self._make_svc()
        mock_ui.objects.filter.return_value.select_related.return_value = [MagicMock()]
        result = svc.get_user_inventory(MagicMock())
        assert len(result) == 1
