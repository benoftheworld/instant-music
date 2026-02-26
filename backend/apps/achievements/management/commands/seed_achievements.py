"""
Management command to seed default achievements.
"""
from django.core.management.base import BaseCommand
from apps.achievements.models import Achievement


DEFAULT_ACHIEVEMENTS = [
    # Games played milestones
    {
        'name': 'Première partie',
        'description': 'Jouer votre première partie',
        'condition_type': 'games_played',
        'condition_value': 1,
        'points': 10,
    },
    {
        'name': 'Habitué',
        'description': 'Jouer 5 parties',
        'condition_type': 'games_played',
        'condition_value': 5,
        'points': 25,
    },
    {
        'name': 'Vétéran',
        'description': 'Jouer 10 parties',
        'condition_type': 'games_played',
        'condition_value': 10,
        'points': 50,
    },
    {
        'name': 'Accro à la musique',
        'description': 'Jouer 25 parties',
        'condition_type': 'games_played',
        'condition_value': 25,
        'points': 100,
    },
    {
        'name': 'Légende',
        'description': 'Jouer 50 parties',
        'condition_type': 'games_played',
        'condition_value': 50,
        'points': 200,
    },
    # Wins milestones
    {
        'name': 'Première victoire',
        'description': 'Remporter votre première victoire',
        'condition_type': 'wins',
        'condition_value': 1,
        'points': 15,
    },
    {
        'name': 'Compétiteur',
        'description': 'Remporter 5 victoires',
        'condition_type': 'wins',
        'condition_value': 5,
        'points': 50,
    },
    {
        'name': 'Champion',
        'description': 'Remporter 10 victoires',
        'condition_type': 'wins',
        'condition_value': 10,
        'points': 100,
    },
    {
        'name': 'Imbattable',
        'description': 'Remporter 25 victoires',
        'condition_type': 'wins',
        'condition_value': 25,
        'points': 200,
    },
    # Points milestones
    {
        'name': 'Premiers pas',
        'description': 'Atteindre 1 000 points au total',
        'condition_type': 'points',
        'condition_value': 1000,
        'points': 10,
    },
    {
        'name': 'Mélomane',
        'description': 'Atteindre 5 000 points au total',
        'condition_type': 'points',
        'condition_value': 5000,
        'points': 50,
    },
    {
        'name': 'Expert musical',
        'description': 'Atteindre 10 000 points au total',
        'condition_type': 'points',
        'condition_value': 10000,
        'points': 100,
    },
    {
        'name': 'Maître de la musique',
        'description': 'Atteindre 50 000 points au total',
        'condition_type': 'points',
        'condition_value': 50000,
        'points': 250,
    },
    # Special achievements
    {
        'name': 'Sans faute',
        'description': 'Répondre correctement à toutes les questions d\'une partie',
        'condition_type': 'perfect_round',
        'condition_value': 1,
        'points': 75,
    },
    {
        'name': 'Série de victoires',
        'description': 'Remporter 3 parties consécutives',
        'condition_type': 'win_streak',
        'condition_value': 3,
        'points': 100,
    },
    {
        'name': 'Invincible',
        'description': 'Remporter 5 parties consécutives',
        'condition_type': 'win_streak',
        'condition_value': 5,
        'points': 200,
    },
]


class Command(BaseCommand):
    help = 'Seed default achievements into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing achievements before seeding',
        )

    def handle(self, *args, **options):
        if options['reset']:
            count = Achievement.objects.count()
            Achievement.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Deleted {count} existing achievements'))

        created_count = 0
        skipped_count = 0
        
        for data in DEFAULT_ACHIEVEMENTS:
            _, created = Achievement.objects.get_or_create(
                name=data['name'],
                defaults=data,
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Seeded achievements: {created_count} created, {skipped_count} already existed'
            )
        )
