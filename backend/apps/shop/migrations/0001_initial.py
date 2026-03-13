"""Migration initiale de l'application boutique.
"""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("games", "0023_gameinvitation"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ShopItem",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=100, verbose_name="nom")),
                ("description", models.TextField(verbose_name="description")),
                (
                    "icon",
                    models.ImageField(
                        blank=True,
                        null=True,
                        upload_to="shop/",
                        verbose_name="icône",
                    ),
                ),
                (
                    "item_type",
                    models.CharField(
                        choices=[
                            ("bonus", "Bonus de jeu"),
                            ("physical", "Produit physique"),
                        ],
                        default="bonus",
                        max_length=20,
                        verbose_name="type d'article",
                    ),
                ),
                (
                    "bonus_type",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("double_points", "Points doublés"),
                            ("max_points", "Points maximum"),
                            ("time_bonus", "Temps bonus (+15 s)"),
                            ("fifty_fifty", "50/50 (retire 2 mauvaises réponses)"),
                            ("steal", "Vol de points (-100 pts au 1er)"),
                            ("shield", "Bouclier (protection vol)"),
                        ],
                        help_text="Uniquement pour les articles de type bonus",
                        max_length=30,
                        null=True,
                        verbose_name="type de bonus",
                    ),
                ),
                (
                    "cost",
                    models.IntegerField(
                        default=0,
                        help_text="0 = gratuit (distribution en événement)",
                        verbose_name="coût (pièces)",
                    ),
                ),
                (
                    "is_event_only",
                    models.BooleanField(
                        default=False,
                        help_text="Produit physique remis gratuitement lors d'une soirée",
                        verbose_name="distribué en événement uniquement",
                    ),
                ),
                (
                    "stock",
                    models.IntegerField(
                        blank=True,
                        help_text="Null = illimité",
                        null=True,
                        verbose_name="stock",
                    ),
                ),
                (
                    "is_available",
                    models.BooleanField(default=True, verbose_name="disponible"),
                ),
                (
                    "sort_order",
                    models.IntegerField(default=0, verbose_name="ordre d'affichage"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="créé le"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="mis à jour le"),
                ),
            ],
            options={
                "verbose_name": "article de la boutique",
                "verbose_name_plural": "articles de la boutique",
                "ordering": ["sort_order", "name"],
            },
        ),
        migrations.CreateModel(
            name="UserInventory",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "quantity",
                    models.IntegerField(default=1, verbose_name="quantité"),
                ),
                (
                    "purchased_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="acheté le"),
                ),
                (
                    "item",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="inventory_entries",
                        to="shop.shopitem",
                        verbose_name="article",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shop_inventory",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="utilisateur",
                    ),
                ),
            ],
            options={
                "verbose_name": "inventaire utilisateur",
                "verbose_name_plural": "inventaires utilisateurs",
                "unique_together": {("user", "item")},
            },
        ),
        migrations.CreateModel(
            name="GameBonus",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "bonus_type",
                    models.CharField(
                        choices=[
                            ("double_points", "Points doublés"),
                            ("max_points", "Points maximum"),
                            ("time_bonus", "Temps bonus (+15 s)"),
                            ("fifty_fifty", "50/50 (retire 2 mauvaises réponses)"),
                            ("steal", "Vol de points (-100 pts au 1er)"),
                            ("shield", "Bouclier (protection vol)"),
                        ],
                        max_length=30,
                        verbose_name="type de bonus",
                    ),
                ),
                (
                    "round_number",
                    models.IntegerField(
                        blank=True,
                        null=True,
                        verbose_name="numéro du round ciblé",
                    ),
                ),
                (
                    "activated_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="activé le"),
                ),
                (
                    "is_used",
                    models.BooleanField(default=False, verbose_name="consommé"),
                ),
                (
                    "used_at",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="consommé le"
                    ),
                ),
                (
                    "game",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bonuses",
                        to="games.game",
                        verbose_name="partie",
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="bonuses",
                        to="games.gameplayer",
                        verbose_name="joueur",
                    ),
                ),
            ],
            options={
                "verbose_name": "bonus en partie",
                "verbose_name_plural": "bonus en partie",
                "ordering": ["-activated_at"],
            },
        ),
    ]
