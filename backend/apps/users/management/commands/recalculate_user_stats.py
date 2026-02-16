"""
Django management command to recalculate user statistics from finished games.
Usage: python manage.py recalculate_user_stats
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Sum, Q
from apps.users.models import User
from apps.games.models import Game, GamePlayer


class Command(BaseCommand):
    help = 'Recalculate user statistics (games played, wins, total points) from finished games'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting user statistics recalculation...'))
        
        users = User.objects.all()
        updated_count = 0
        
        for user in users:
            # Get all finished game participations for this user
            participations = GamePlayer.objects.filter(
                user=user,
                game__status='finished'
            )
            
            # Calculate stats
            total_games = participations.count()
            total_wins = participations.filter(rank=1).count()
            total_points = participations.aggregate(total=Sum('score'))['total'] or 0
            
            # Update user
            user.total_games_played = total_games
            user.total_wins = total_wins
            user.total_points = total_points
            user.save()
            
            updated_count += 1
            
            if total_games > 0:
                self.stdout.write(
                    f'  {user.username}: {total_games} parties, {total_wins} victoires, {total_points} points'
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully recalculated statistics for {updated_count} users.')
        )
