"""Commande de gestion pour pré-remplir la boutique avec les articles par défaut.

Usage: python manage.py seed_shop [--force]
"""

from django.core.management.base import BaseCommand

from apps.shop.models import BonusType, ItemType, ShopItem

# ─── Catalogue par défaut ──────────────────────────────────────────────────────
BONUS_ITEMS = [
    {
        "name": "Points Doublés",
        "description": (
            "Double vos points sur le prochain round où vous répondez correctement. "
            "Activez-le n'importe quand durant la partie !"
        ),
        "item_type": ItemType.BONUS,
        "bonus_type": BonusType.DOUBLE_POINTS,
        "cost": 50,
        "sort_order": 10,
    },
    {
        "name": "Points Maximum",
        "description": (
            "Obtenez 100 points (score maximum de base) sur votre prochain round correct, "
            "peu importe votre temps de réponse. Parfait pour les indécis !"
        ),
        "item_type": ItemType.BONUS,
        "bonus_type": BonusType.MAX_POINTS,
        "cost": 80,
        "sort_order": 20,
    },
    {
        "name": "Temps Bonus",
        "description": (
            "+15 secondes sur le timer du round en cours. "
            "Tout le monde en profite — utilisez-le avec stratégie !"
        ),
        "item_type": ItemType.BONUS,
        "bonus_type": BonusType.TIME_BONUS,
        "cost": 40,
        "sort_order": 30,
    },
    {
        "name": "50/50",
        "description": (
            "Deux mauvaises réponses disparaissent de vos choix pour le round en cours. "
            "Ne fonctionne qu'en mode QCM."
        ),
        "item_type": ItemType.BONUS,
        "bonus_type": BonusType.FIFTY_FIFTY,
        "cost": 60,
        "sort_order": 40,
    },
    {
        "name": "Vol de Points",
        "description": (
            "Vole 100 points au joueur en tête du classement à la fin du round "
            "(contrecarré par un Bouclier actif)."
        ),
        "item_type": ItemType.BONUS,
        "bonus_type": BonusType.STEAL,
        "cost": 100,
        "sort_order": 50,
    },
    {
        "name": "Bouclier",
        "description": (
            "Protège vos points contre le prochain Vol de Points adverse. "
            "Le bouclier se consume automatiquement en se déclenchant."
        ),
        "item_type": ItemType.BONUS,
        "bonus_type": BonusType.SHIELD,
        "cost": 70,
        "sort_order": 60,
    },
    {
        "name": "Mode Brouillard",
        "description": (
            "Floute les options de réponse QCM de tous les adversaires pendant 5 secondes "
            "au début du prochain round. Vous seul voyez clair — jouez stratégiquement !"
        ),
        "item_type": ItemType.BONUS,
        "bonus_type": BonusType.FOG,
        "cost": 80,
        "sort_order": 65,
    },
    {
        "name": "Joker",
        "description": (
            "Répondez faux et obtenez quand même des points comme si c'était correct "
            "(basés sur votre temps de réponse). Sans bonus de streak ni de classement."
        ),
        "item_type": ItemType.BONUS,
        "bonus_type": BonusType.JOKER,
        "cost": 120,
        "sort_order": 70,
    },
]

PHYSICAL_ITEMS = [
    {
        "name": "T-shirt InstantMusic",
        "description": (
            "T-shirt exclusif InstantMusic — disponible uniquement lors des soirées "
            "événement. Récupère-le gratuitement sur place !"
        ),
        "item_type": ItemType.PHYSICAL,
        "bonus_type": None,
        "cost": 0,
        "is_event_only": True,
        "sort_order": 100,
    },
    {
        "name": "Pack de stickers",
        "description": (
            "Un lot de stickers aux couleurs d'InstantMusic. "
            "Offert gratuitement lors des soirées événement."
        ),
        "item_type": ItemType.PHYSICAL,
        "bonus_type": None,
        "cost": 0,
        "is_event_only": True,
        "sort_order": 110,
    },
    {
        "name": "Tote bag InstantMusic",
        "description": (
            "Tote bag en coton avec le logo InstantMusic. "
            "Distribué lors des soirées événement en édition limitée."
        ),
        "item_type": ItemType.PHYSICAL,
        "bonus_type": None,
        "cost": 0,
        "is_event_only": True,
        "sort_order": 120,
    },
    {
        "name": "Badge collector",
        "description": (
            "Badge en métal édition collector — chaque soirée a son badge unique. "
            "Récupérez-le gratuitement en événement."
        ),
        "item_type": ItemType.PHYSICAL,
        "bonus_type": None,
        "cost": 0,
        "is_event_only": True,
        "sort_order": 130,
    },
]
# ──────────────────────────────────────────────────────────────────────────────


class Command(BaseCommand):
    help = "Pré-remplir la boutique avec les articles par défaut"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recréer les articles existants (mise à jour)",
        )

    def handle(self, *args, **options):
        force = options["force"]
        created_count = 0
        updated_count = 0

        all_items = BONUS_ITEMS + PHYSICAL_ITEMS

        for item_data in all_items:
            item_type = item_data["item_type"]
            bonus_type = item_data.get("bonus_type")

            # Identifier l'article de façon unique par nom
            obj, created = ShopItem.objects.get_or_create(
                name=item_data["name"],
                defaults={
                    "description": item_data["description"],
                    "item_type": item_type,
                    "bonus_type": bonus_type,
                    "cost": item_data["cost"],
                    "is_event_only": item_data.get("is_event_only", False),
                    "sort_order": item_data["sort_order"],
                    "is_available": True,
                },
            )

            if not created and force:
                obj.description = item_data["description"]
                obj.item_type = item_type
                obj.bonus_type = bonus_type
                obj.cost = item_data["cost"]
                obj.is_event_only = item_data.get("is_event_only", False)
                obj.sort_order = item_data["sort_order"]
                obj.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"  ↻ Mis à jour : {obj.name}"))
            elif created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  ✓ Créé : {obj.name}"))
            else:
                self.stdout.write(f"  — Déjà existant : {obj.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nBoutique : {created_count} créé(s), {updated_count} mis à jour."
            )
        )
