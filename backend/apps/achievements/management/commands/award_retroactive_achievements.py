"""
Management command to retroactively check and award achievements for all users.
"""

from django.core.management.base import BaseCommand

from apps.achievements.services import achievement_service
from apps.games.models import GameAnswer, GamePlayer
from apps.users.models import User


class Command(BaseCommand):
    """Retroactively check and award achievements for all users."""

    help = "Retroactively check and award achievements for all users"

    def handle(self, *args, **options):
        """Check all users and award achievements based on their past game.

        For simplicity, this example only checks for the "Perfect Game"
        achievement, which requires a user to have at least one game where
        they answered all questions correctly.
        """
        users = User.objects.filter(total_games_played__gt=0)
        total_awarded = 0

        for user in users:
            # Check if user ever had a perfect game
            perfect_game = False
            game_players = GamePlayer.objects.filter(
                user=user, rank__isnull=False
            )
            for gp in game_players:
                game = gp.game
                total_rounds = game.rounds.count()
                if total_rounds > 0:
                    correct = GameAnswer.objects.filter(
                        player=gp,
                        round__game=game,
                        is_correct=True,
                    ).count()
                    if correct == total_rounds:
                        perfect_game = True
                        break

            round_data = {"perfect_game": perfect_game}
            awarded = achievement_service.check_and_award(
                user, round_data=round_data
            )

            if awarded:
                names = [a.name for a in awarded]
                self.stdout.write(
                    self.style.SUCCESS(f"{user.username}: awarded {names}")
                )
                total_awarded += len(awarded)
            else:
                self.stdout.write(f"{user.username}: no new achievements")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nTotal achievements awarded: {total_awarded}"
            )
        )
