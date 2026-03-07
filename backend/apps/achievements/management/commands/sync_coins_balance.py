"""Commande de synchronisation du solde de pièces (coins_balance).

Recalcule le solde de chaque utilisateur à partir :
  - des achievements déjà débloqués (points de chaque UserAchievement)
  - diminué des achats effectués en boutique
  (quantité * coût de chaque article)

Usage :
    make dev-shell
    python manage.py sync_coins_balance [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.db.models import F, Sum

from apps.achievements.models import UserAchievement
from apps.shop.models import UserInventory
from apps.users.models import User


class Command(BaseCommand):
    """Resynchronise coins_balance pour tous les utilisateurs."""

    help = (
        "Recalcule coins_balance à partir des achievements débloqués "
        "et des achats en boutique."
    )

    def add_arguments(self, parser):
        """Ajoute l'argument optionnel --dry-run pour simuler sans persister.

        Arguments :
            parser : ArgumentParser fourni par Django pour définir les
            options de la commande.
        """
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simule les modifications sans les persister en base.",
        )

    def handle(self, *args, **options):
        """Effectue la synchro des soldes de pièces pour tous les utilisateurs.

        Pour chaque utilisateur, calcule le solde attendu et compare avec le
        solde actuel. Affiche les changements et met à jour en base si
        --dry-run n'est pas activé.

        Arguments :
        - args : Arguments positionnels (non utilisés ici).
        - options : Dictionnaire des options, notamment 'dry_run' pour indiquer
          si la commande doit simuler ou appliquer les changements.

        Affiche un résumé à la fin avec le nombre d'utilisateurs mis à jour et
        inchangés.
        """
        dry_run: bool = options["dry_run"]
        verb = "SIMULATION" if dry_run else "MISE À JOUR"

        self.stdout.write(
            self.style.WARNING(
                f"[{verb}] Synchronisation des soldes de pièces…\n"
            )
        )

        users = User.objects.all()
        total_updated = 0
        total_unchanged = 0

        for user in users:
            # 1. Total des points issus des achievements débloqués
            achievement_coins: int = (
                UserAchievement.objects.filter(user=user).aggregate(
                    total=Sum("achievement__points")
                )["total"]
                or 0
            )

            # 2. Total des pièces dépensées en boutique (quantité × coût)
            spent: int = (
                UserInventory.objects.filter(user=user)
                .annotate(line_cost=F("quantity") * F("item__cost"))
                .aggregate(total=Sum("line_cost"))["total"]
                or 0
            )

            # 3. Solde théorique (jamais négatif)
            expected_balance = max(0, achievement_coins - spent)
            current_balance = user.coins_balance

            if expected_balance != current_balance:
                delta = expected_balance - current_balance
                sign = "+" if delta >= 0 else ""
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  {user.username}: {current_balance} "
                        f" → {expected_balance} "
                        f"({sign}{delta}) "
                        f"[achievements={achievement_coins}, dépensé={spent}]"
                    )
                )
                if not dry_run:
                    User.objects.filter(pk=user.pk).update(
                        coins_balance=expected_balance
                    )
                total_updated += 1
            else:
                total_unchanged += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"[{verb}] Terminé — {total_updated}"
                f" utilisateur(s) mis à jour, "
                f"{total_unchanged} inchangé(s)."
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Mode simulation : aucune modification persistée. "
                    "Relancez sans --dry-run pour appliquer."
                )
            )
