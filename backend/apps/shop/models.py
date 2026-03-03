"""
Modèles de la boutique.

ShopItem        — Article disponible dans la boutique (bonus ou produit physique)
UserInventory   — Inventaire de l'utilisateur (articles achetés)
GameBonus       — Bonus activé par un joueur lors d'une partie
"""

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class BonusType(models.TextChoices):
    """Types de bonus utilisables en partie."""

    DOUBLE_POINTS = "double_points", _("Points doublés")
    MAX_POINTS = "max_points", _("Points maximum")
    TIME_BONUS = "time_bonus", _("Temps bonus (+15 s)")
    FIFTY_FIFTY = "fifty_fifty", _("50/50 (retire 2 mauvaises réponses)")
    STEAL = "steal", _("Vol de points (-100 pts au 1er)")
    SHIELD = "shield", _("Bouclier (protection vol)")


class ItemType(models.TextChoices):
    """Catégories d'articles de la boutique."""

    BONUS = "bonus", _("Bonus de jeu")
    PHYSICAL = "physical", _("Produit physique")


class ShopItem(models.Model):
    """Article disponible à l'achat dans la boutique virtuelle."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(_("nom"), max_length=100)
    description = models.TextField(_("description"))
    icon = models.ImageField(
        _("icône"), upload_to="shop/", null=True, blank=True
    )

    item_type = models.CharField(
        _("type d'article"),
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.BONUS,
    )
    bonus_type = models.CharField(
        _("type de bonus"),
        max_length=30,
        choices=BonusType.choices,
        null=True,
        blank=True,
        help_text=_("Uniquement pour les articles de type bonus"),
    )

    # Prix en pièces (0 pour les produits physiques distribués lors d'événements)
    cost = models.IntegerField(
        _("coût (pièces)"),
        default=0,
        help_text=_("0 = gratuit (distribution en événement)"),
    )

    # Produits physiques uniquement
    is_event_only = models.BooleanField(
        _("distribué en événement uniquement"),
        default=False,
        help_text=_("Produit physique remis gratuitement lors d'une soirée"),
    )

    # Gestion du stock (null = illimité)
    stock = models.IntegerField(
        _("stock"),
        null=True,
        blank=True,
        help_text=_("Null = illimité"),
    )

    is_available = models.BooleanField(_("disponible"), default=True)
    sort_order = models.IntegerField(_("ordre d'affichage"), default=0)
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("article de la boutique")
        verbose_name_plural = _("articles de la boutique")
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.cost} pièces)"

    @property
    def is_in_stock(self) -> bool:
        """Vérifie si l'article est disponible en stock."""
        if self.stock is None:
            return True
        return self.stock > 0


class UserInventory(models.Model):
    """Inventaire de l'utilisateur — articles achetés ou obtenus."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shop_inventory",
        verbose_name=_("utilisateur"),
    )
    item = models.ForeignKey(
        ShopItem,
        on_delete=models.CASCADE,
        related_name="inventory_entries",
        verbose_name=_("article"),
    )
    quantity = models.IntegerField(_("quantité"), default=1)
    purchased_at = models.DateTimeField(_("acheté le"), auto_now_add=True)

    class Meta:
        verbose_name = _("inventaire utilisateur")
        verbose_name_plural = _("inventaires utilisateurs")
        unique_together = ["user", "item"]

    def __str__(self) -> str:
        return f"{self.user.username} — {self.item.name} x{self.quantity}"


class GameBonus(models.Model):
    """Bonus activé par un joueur au cours d'une partie."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    game = models.ForeignKey(
        "games.Game",
        on_delete=models.CASCADE,
        related_name="bonuses",
        verbose_name=_("partie"),
    )
    player = models.ForeignKey(
        "games.GamePlayer",
        on_delete=models.CASCADE,
        related_name="bonuses",
        verbose_name=_("joueur"),
    )
    bonus_type = models.CharField(
        _("type de bonus"),
        max_length=30,
        choices=BonusType.choices,
    )

    # Round cible (null = prochain round disponible)
    round_number = models.IntegerField(
        _("numéro du round ciblé"),
        null=True,
        blank=True,
    )

    activated_at = models.DateTimeField(_("activé le"), auto_now_add=True)
    is_used = models.BooleanField(_("consommé"), default=False)
    used_at = models.DateTimeField(_("consommé le"), null=True, blank=True)

    class Meta:
        verbose_name = _("bonus en partie")
        verbose_name_plural = _("bonus en partie")
        ordering = ["-activated_at"]

    def __str__(self) -> str:
        return (
            f"{self.player.user.username} — {self.bonus_type} "
            f"(round {self.round_number})"
        )
