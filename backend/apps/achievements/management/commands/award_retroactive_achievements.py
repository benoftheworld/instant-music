"""
Management command to retroactively check and award achievements for all users.
"""
from django.core.management.base import BaseCommand
from apps.users.models import User
from apps.achievements.services import achievement_service
from apps.games.models import GamePlayer, GameAnswer


class Command(BaseCommand):
    help = 'Retroactively check and award achievements for all users'

    def handle(self, *args, **options):
        users = User.objects.filter(total_games_played__gt=0)
        total_awarded = 0
        
        for user in users:
            # Check if user ever had a perfect game
            perfect_game = False
            game_players = GamePlayer.objects.filter(user=user, rank__isnull=False)
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
            
            round_data = {'perfect_game': perfect_game}
            awarded = achievement_service.check_and_award(user, round_data=round_data)
            
            if awarded:
                names = [a.name for a in awarded]
                self.stdout.write(
                    self.style.SUCCESS(f'{user.username}: awarded {names}')
                )
                total_awarded += len(awarded)
            else:
                self.stdout.write(f'{user.username}: no new achievements')
        
        self.stdout.write(
            self.style.SUCCESS(f'\nTotal achievements awarded: {total_awarded}')
        )
