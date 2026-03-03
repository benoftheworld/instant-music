"""
Services métier de la boutique.

ShopService  — gestion des achats et de l'inventaire
BonusService — activation et consommation des bonus en partie
"""

import logging
from typing import Optional

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import BonusType, GameBonus, ShopItem, UserInventory

logger = logging.getLogger("apps.shop.services")


class InsufficientCoinsError(Exception):
    """Exception levée quand le joueur n'a pas assez de pièces."""


class ItemNotAvailableError(Exception):
    """Exception levée quand l'article n'est pas disponible."""


class BonusAlreadyActiveError(Exception):
    """Exception levée quand un bonus du même type est déjà actif."""


class ShopService:
    """Service de gestion de la boutique et des achats."""

    @transaction.atomic
    def purchase(
        self, user, item_id: str, quantity: int = 1
    ) -> UserInventory:
        """
        Acheter un article de la boutique.

        Déduit les pièces du solde de l'utilisateur et incrémente l'inventaire.
        """
        try:
            item = ShopItem.objects.select_for_update().get(
                id=item_id, is_available=True
            )
        except ShopItem.DoesNotExist:
            raise ItemNotAvailableError(
                _("Cet article n'est pas disponible.")
            )

        # Les produits physiques d'événement ne peuvent être achetés en boutique
        if item.is_event_only:
            raise ItemNotAvailableError(
                _(
                    "Ce produit physique est distribué gratuitement lors "
                    "d'une soirée événement. Il ne peut pas être acheté."
                )
            )

        # Vérification du stock
        if item.stock is not None:
            if item.stock < quantity:
                raise ItemNotAvailableError(
                    _("Stock insuffisant pour cet article.")
                )

        total_cost = item.cost * quantity

        # Vérification du solde
        if user.coins_balance < total_cost:
            raise InsufficientCoinsError(
                _(
                    f"Solde insuffisant. Vous avez {user.coins_balance} pièces, "
                    f"il en faut {total_cost}."
                )
            )

        # Déduction des pièces
        user.coins_balance -= total_cost
        user.save(update_fields=["coins_balance"])

        # Mise à jour du stock
        if item.stock is not None:
            item.stock -= quantity
            item.save(update_fields=["stock"])

        # Mise à jour de l'inventaire
        inventory, created = UserInventory.objects.get_or_create(
            user=user,
            item=item,
            defaults={"quantity": quantity},
        )
        if not created:
            inventory.quantity += quantity
            inventory.save(update_fields=["quantity"])

        logger.info(
            "shop_purchase",
            extra={
                "user_id": str(user.id),
                "item_id": str(item.id),
                "item_name": item.name,
                "quantity": quantity,
                "cost": total_cost,
                "coins_remaining": user.coins_balance,
            },
        )

        return inventory

    def get_user_inventory(self, user):
        """Récupérer l'inventaire complet d'un utilisateur."""
        return UserInventory.objects.filter(user=user, quantity__gt=0).select_related(
            "item"
        )

    def get_total_coins_available(self) -> int:
        """
        Retourne le total de pièces qu'un joueur peut obtenir en débloquant
        tous les achievements existants.
        Utilisé pour afficher le total max dans la boutique.
        """
        from apps.achievements.models import Achievement

        return Achievement.objects.aggregate(
            total=models_Sum("points")
        )["total"] or 0


class BonusService:
    """Service d'activation et de vérification des bonus en partie."""

    # Bonus qui ne peuvent être actifs qu'une seule fois à la fois
    UNIQUE_BONUSES = {BonusType.SHIELD}

    # Durée ajoutée (secondes) par le bonus TIME_BONUS
    TIME_BONUS_SECONDS = 15

    # Points volés par le bonus STEAL
    STEAL_POINTS = 100

    @transaction.atomic
    def activate_bonus(
        self,
        user,
        game,
        bonus_type: str,
        round_number: Optional[int] = None,
    ) -> GameBonus:
        """
        Activer un bonus en partie.

        Consomme 1 exemplaire dans l'inventaire du joueur et crée un
        enregistrement GameBonus.
        """
        from apps.games.models import GamePlayer

        # Vérification que le joueur participe à la partie
        try:
            player = GamePlayer.objects.get(game=game, user=user)
        except GamePlayer.DoesNotExist:
            raise ValueError(_("Vous ne participez pas à cette partie."))

        # Vérification de l'inventaire
        try:
            item = ShopItem.objects.get(
                bonus_type=bonus_type, item_type="bonus", is_available=True
            )
            inventory = UserInventory.objects.select_for_update().get(
                user=user, item=item, quantity__gt=0
            )
        except (ShopItem.DoesNotExist, UserInventory.DoesNotExist):
            raise ItemNotAvailableError(
                _("Vous ne possédez pas ce bonus dans votre inventaire.")
            )

        # Vérification unicité (ex : bouclier)
        if bonus_type in self.UNIQUE_BONUSES:
            already_active = GameBonus.objects.filter(
                game=game,
                player=player,
                bonus_type=bonus_type,
                is_used=False,
            ).exists()
            if already_active:
                raise BonusAlreadyActiveError(
                    _("Ce bonus est déjà actif pour ce round.")
                )

        # Consommer l'inventaire
        inventory.quantity -= 1
        inventory.save(update_fields=["quantity"])

        # Créer le bonus actif
        game_bonus = GameBonus.objects.create(
            game=game,
            player=player,
            bonus_type=bonus_type,
            round_number=round_number,
        )

        logger.info(
            "bonus_activated",
            extra={
                "user_id": str(user.id),
                "game_id": str(game.id),
                "bonus_type": bonus_type,
                "round_number": round_number,
            },
        )

        return game_bonus

    def get_active_bonuses_for_player(self, player, round_number: int):
        """Récupérer les bonus actifs pour un joueur à un round donné."""
        return GameBonus.objects.filter(
            player=player,
            round_number=round_number,
            is_used=False,
        )

    def consume_bonus(self, game_bonus: GameBonus) -> None:
        """Marquer un bonus comme consommé."""
        game_bonus.is_used = True
        game_bonus.used_at = timezone.now()
        game_bonus.save(update_fields=["is_used", "used_at"])

    def apply_score_bonuses(
        self,
        player,
        round_number: int,
        base_points: int,
        is_correct: bool,
        game,
    ) -> tuple[int, list[str]]:
        """
        Appliquer les bonus de score actifs pour un joueur sur un round.

        Retourne (points_finaux, liste_des_bonus_appliqués).
        """
        if not is_correct:
            return base_points, []

        active_bonus_types = []
        bonus_qs = GameBonus.objects.filter(
            game=game,
            player=player,
            round_number=round_number,
            is_used=False,
            bonus_type__in=[
                BonusType.DOUBLE_POINTS,
                BonusType.MAX_POINTS,
            ],
        ).select_for_update()

        final_points = base_points

        for game_bonus in bonus_qs:
            if game_bonus.bonus_type == BonusType.DOUBLE_POINTS:
                final_points = final_points * 2
                active_bonus_types.append(BonusType.DOUBLE_POINTS)
                self.consume_bonus(game_bonus)

            elif game_bonus.bonus_type == BonusType.MAX_POINTS:
                from apps.games.services import SCORE_BASE_POINTS

                final_points = max(final_points, SCORE_BASE_POINTS * 2)
                active_bonus_types.append(BonusType.MAX_POINTS)
                self.consume_bonus(game_bonus)

        return final_points, active_bonus_types

    def get_fifty_fifty_exclusions(
        self, player, round_number: int, options: list[str], correct_answer: str
    ) -> list[str]:
        """
        Retourne les 2 mauvaises réponses à masquer pour le 50/50.
        Consomme le bonus si présent.
        """
        bonus_qs = GameBonus.objects.filter(
            player=player,
            round_number=round_number,
            bonus_type=BonusType.FIFTY_FIFTY,
            is_used=False,
        )
        if not bonus_qs.exists():
            return []

        wrong = [o for o in options if o != correct_answer]
        import random

        excluded = random.sample(wrong, min(2, len(wrong)))

        for b in bonus_qs:
            self.consume_bonus(b)

        return excluded

    def apply_steal_bonus(
        self, player, game, round_number: int
    ) -> int:
        """
        Applique le bonus 'vol de points' :
        Vole STEAL_POINTS au joueur en tête (si bouclier absent).
        Retourne les points volés (0 si personne à voler ou bouclier actif).
        """
        from apps.games.models import GamePlayer

        bonus_qs = GameBonus.objects.filter(
            player=player,
            round_number=round_number,
            bonus_type=BonusType.STEAL,
            is_used=False,
        )
        if not bonus_qs.exists():
            return 0

        # Trouver le leader (exclu soi-même)
        leader = (
            GamePlayer.objects.filter(game=game)
            .exclude(id=player.id)
            .order_by("-score")
            .first()
        )
        if not leader:
            for b in bonus_qs:
                self.consume_bonus(b)
            return 0

        # Vérifier si le leader a un bouclier actif
        has_shield = GameBonus.objects.filter(
            player=leader,
            round_number=round_number,
            bonus_type=BonusType.SHIELD,
            is_used=False,
        ).exists()

        if has_shield:
            # Consommer le bouclier du leader
            GameBonus.objects.filter(
                player=leader,
                round_number=round_number,
                bonus_type=BonusType.SHIELD,
                is_used=False,
            ).update(is_used=True, used_at=timezone.now())
            for b in bonus_qs:
                self.consume_bonus(b)
            return 0

        # Applique le vol
        stolen = min(self.STEAL_POINTS, leader.score)
        leader.score = max(0, leader.score - stolen)
        player.score += stolen
        leader.save(update_fields=["score"])
        player.save(update_fields=["score"])

        for b in bonus_qs:
            self.consume_bonus(b)

        logger.info(
            "steal_bonus_applied",
            extra={
                "thief": str(player.user.id),
                "victim": str(leader.user.id),
                "stolen": stolen,
                "game_id": str(game.id),
            },
        )

        return stolen


# Imports tardifs pour éviter les dépendances circulaires
from django.db.models import Sum as models_Sum  # noqa: E402

# Singletons
shop_service = ShopService()
bonus_service = BonusService()
