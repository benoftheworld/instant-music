"""Management command to recalculate denormalized team stats from member data."""

from django.core.management.base import BaseCommand
from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.users.models import Team


class Command(BaseCommand):
    help = "Recalcule les stats dénormalisées de toutes les équipes à partir des stats des membres."

    def handle(self, *args, **options):
        teams = Team.objects.all()
        updated = 0

        for team in teams:
            aggregated = team.members.aggregate(
                sum_games=Coalesce(Sum("total_games_played"), 0),
                sum_wins=Coalesce(Sum("total_wins"), 0),
                sum_points=Coalesce(Sum("total_points"), 0),
            )

            team.total_games = aggregated["sum_games"]
            team.total_wins = aggregated["sum_wins"]
            team.total_points = aggregated["sum_points"]
            team.save(update_fields=["total_games", "total_wins", "total_points"])
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"{updated} équipe(s) mise(s) à jour.")
        )
