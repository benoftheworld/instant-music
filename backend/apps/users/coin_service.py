"""Service centralisé pour la gestion des pièces (coins).

Toutes les opérations de crédit/débit de pièces passent par ce module
afin de garantir l'atomicité (F expressions) et la traçabilité.
"""

import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import F

logger = logging.getLogger("apps.users.coin_service")

User = get_user_model()


class InsufficientCoinsError(Exception):
    """Le joueur n'a pas assez de pièces."""


@transaction.atomic
def add_coins(user_id: int, amount: int, reason: str) -> int:
    """Crédite des pièces au joueur de manière atomique.

    Returns:
        Le nouveau solde après crédit.

    """
    if amount <= 0:
        return get_balance(user_id)

    User.objects.filter(pk=user_id).update(coins_balance=F("coins_balance") + amount)
    balance = get_balance(user_id)
    logger.info(
        "coins_added user=%s amount=%d reason=%s balance=%d",
        user_id,
        amount,
        reason,
        balance,
    )
    return balance


@transaction.atomic
def deduct_coins(user_id: int, amount: int, reason: str) -> int:
    """Débite des pièces du joueur de manière atomique.

    Raises:
        InsufficientCoinsError: si le solde est insuffisant.

    Returns:
        Le nouveau solde après débit.

    """
    if amount <= 0:
        return get_balance(user_id)

    # select_for_update empêche les lectures concurrentes
    user = User.objects.select_for_update().get(pk=user_id)
    if user.coins_balance < amount:
        raise InsufficientCoinsError(
            f"Solde insuffisant. Vous avez {user.coins_balance} pièces, "
            f"il en faut {amount}."
        )

    User.objects.filter(pk=user_id).update(coins_balance=F("coins_balance") - amount)
    balance = get_balance(user_id)
    logger.info(
        "coins_deducted user=%s amount=%d reason=%s balance=%d",
        user_id,
        amount,
        reason,
        balance,
    )
    return balance


def get_balance(user_id: int) -> int:
    """Retourne le solde actuel de pièces (lecture fraîche)."""
    return (
        User.objects.filter(pk=user_id).values_list("coins_balance", flat=True).first()
        or 0
    )
