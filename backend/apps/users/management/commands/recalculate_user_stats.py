"""Django management command to recalculate user statistics from finished games.

Usage: python manage.py recalculate_user_stats.
"""

from django.core.management.base import BaseCommand
from django.db.models import Q, Sum

from apps.games.models import GamePlayer
from apps.users.models import User


class Command(BaseCommand):
    """Commande de gestion pour recalculer les statistiques des utilisateurs."""

    help = (
        "Recalculate user statistics (games played, wins, total points)"
        " from finished games"
    )

    def handle(self, *args, **options):
        """Recalculate statistics for all users from finished game records."""
        self.stdout.write(
            self.style.NOTICE("Starting user statistics recalculation...")
        )

        users = User.objects.all()
        updated_count = 0

        for user in users:
            # Get all finished game participations for this user
            participations = GamePlayer.objects.filter(
                user=user, game__status="finished"
            )

            # Calculate stats
            total_games = participations.count()
            # Victoires : uniquement les parties multijoueur (is_online=True)
            total_wins = participations.filter(rank=1, game__is_online=True).count()
            # Points : exclure les parties solo sauf karaoké
            total_points = (
                participations.filter(
                    Q(game__is_online=True) | Q(game__mode="karaoke")
                ).aggregate(total=Sum("score"))["total"]
                or 0
            )

            # Update user
            user.total_games_played = total_games
            user.total_wins = total_wins
            user.total_points = total_points
            user.save(
                update_fields=["total_games_played", "total_wins", "total_points"]
            )

            updated_count += 1

            if total_games > 0:
                self.stdout.write(
                    f"  {user.username}: {total_games} parties,"
                    f" {total_wins} victoires, {total_points} points"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"\nSuccessfully recalculated statistics for {updated_count} users."
            )
        )
