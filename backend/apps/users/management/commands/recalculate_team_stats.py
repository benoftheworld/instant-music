"""Management command to recalculate denormalized team stats from GamePlayer records.

Déduplique les stats par partie : si deux membres jouent la même partie,
celle-ci ne compte qu'une seule fois dans total_games et total_wins.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q, Sum

from apps.games.models import GamePlayer
from apps.users.models import Team


class Command(BaseCommand):
    """Commande de gestion pour recalculer les stats dénormalisées des équipes."""

    help = (
        "Recalcule les stats dénormalisées de toutes les équipes"
        " (dédupliquées par partie)."
    )

    def handle(self, *args, **options):
        """Recalculate denormalized stats for all teams."""
        teams = Team.objects.all()
        updated = 0

        for team in teams:
            member_ids = set(team.members.values_list("id", flat=True))

            all_participations = GamePlayer.objects.filter(
                user_id__in=member_ids,
                game__status="finished",
            )

            # Parties distinctes avec au moins un membre
            team.total_games = (
                all_participations.values("game_id").distinct().count()
            )

            # Victoires : parties distinctes où un membre est 1er (hors solo)
            team.total_wins = (
                all_participations.filter(rank=1, game__is_online=True)
                .values("game_id")
                .distinct()
                .count()
            )

            # Points : somme des scores des membres (hors solo non-karaoké)
            team.total_points = (
                all_participations.filter(
                    Q(game__is_online=True) | Q(game__mode="karaoke")
                ).aggregate(s=Sum("score"))["s"]
                or 0
            )

            team.save(update_fields=["total_games", "total_wins", "total_points"])
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"{updated} équipe(s) mise(s) à jour.")
        )
