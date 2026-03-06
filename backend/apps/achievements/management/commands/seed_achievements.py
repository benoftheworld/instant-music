"""Management command to seed default achievements.

This command populates the database with a predefined set of achievements that
users can earn by playing the game. It includes milestones for games played,
wins, points, and special conditions like perfect rounds or win streaks.
The command also supports an optional --reset flag to clear existing
achievements before seeding new ones.
"""

from django.core.management.base import BaseCommand

from apps.achievements.models import Achievement

DEFAULT_ACHIEVEMENTS = [
    # Games played milestones
    {
        "name": "Première partie",
        "description": "Jouer votre première partie",
        "condition_type": "games_played",
        "condition_value": 1,
        "points": 10,
    },
    {
        "name": "Habitué",
        "description": "Jouer 5 parties",
        "condition_type": "games_played",
        "condition_value": 5,
        "points": 25,
    },
    {
        "name": "Vétéran",
        "description": "Jouer 10 parties",
        "condition_type": "games_played",
        "condition_value": 10,
        "points": 50,
    },
    {
        "name": "Accro à la musique",
        "description": "Jouer 25 parties",
        "condition_type": "games_played",
        "condition_value": 25,
        "points": 100,
    },
    {
        "name": "Légende",
        "description": "Jouer 50 parties",
        "condition_type": "games_played",
        "condition_value": 50,
        "points": 200,
    },
    # Wins milestones
    {
        "name": "Première victoire",
        "description": "Remporter votre première victoire",
        "condition_type": "wins",
        "condition_value": 1,
        "points": 15,
    },
    {
        "name": "Compétiteur",
        "description": "Remporter 5 victoires",
        "condition_type": "wins",
        "condition_value": 5,
        "points": 50,
    },
    {
        "name": "Champion",
        "description": "Remporter 10 victoires",
        "condition_type": "wins",
        "condition_value": 10,
        "points": 100,
    },
    {
        "name": "Imbattable",
        "description": "Remporter 25 victoires",
        "condition_type": "wins",
        "condition_value": 25,
        "points": 200,
    },
    # Points milestones
    {
        "name": "Premiers pas",
        "description": "Atteindre 1 000 points au total",
        "condition_type": "points",
        "condition_value": 1000,
        "points": 10,
    },
    {
        "name": "Mélomane",
        "description": "Atteindre 5 000 points au total",
        "condition_type": "points",
        "condition_value": 5000,
        "points": 50,
    },
    {
        "name": "Expert musical",
        "description": "Atteindre 10 000 points au total",
        "condition_type": "points",
        "condition_value": 10000,
        "points": 100,
    },
    {
        "name": "Maître de la musique",
        "description": "Atteindre 50 000 points au total",
        "condition_type": "points",
        "condition_value": 50000,
        "points": 250,
    },
    # Special achievements
    {
        "name": "Sans faute",
        "description": "Répondre correctement à toutes les questions d'une partie",
        "condition_type": "perfect_round",
        "condition_value": 1,
        "points": 75,
    },
    {
        "name": "Série de victoires",
        "description": "Remporter 3 parties consécutives",
        "condition_type": "win_streak",
        "condition_value": 3,
        "points": 100,
    },
    {
        "name": "Invincible",
        "description": "Remporter 5 parties consécutives",
        "condition_type": "win_streak",
        "condition_value": 5,
        "points": 200,
    },
    # Vitesse
    {
        "name": "Éclair",
        "description": "Répondre correctement en moins de 5 secondes, 10 fois",
        "condition_type": "fast_answers",
        "condition_value": 10,
        "condition_extra": "5.0",
        "points": 30,
    },
    {
        "name": "Fulgurant",
        "description": "Répondre correctement en moins de 3 secondes, 5 fois",
        "condition_type": "fast_answers",
        "condition_value": 5,
        "condition_extra": "3.0",
        "points": 50,
    },
    {
        "name": "Réflexes de pro",
        "description": "Répondre à toutes les questions en moins de 2 secondes sur une partie parfaite",
        "condition_type": "all_fast_round",
        "condition_value": 1,
        "condition_extra": "2.0",
        "points": 100,
    },
    # Précision
    {
        "name": "Sniper",
        "description": "Atteindre 80% de précision sur au moins 20 parties",
        "condition_type": "accuracy",
        "condition_value": 80,
        "condition_extra": "20",
        "points": 75,
    },
    {
        "name": "Infaillible",
        "description": "Enchaîner 10 bonnes réponses consécutives dans une même partie",
        "condition_type": "global_correct_streak",
        "condition_value": 10,
        "points": 60,
    },
    {
        "name": "Score parfait",
        "description": "Marquer 1 000 points dans une seule partie",
        "condition_type": "single_game_score",
        "condition_value": 1000,
        "points": 80,
    },
    # Modes de jeu
    {
        "name": "Fan de classiques",
        "description": "Jouer 10 parties en mode Classique",
        "condition_type": "games_by_mode",
        "condition_value": 10,
        "condition_extra": "classique",
        "points": 30,
    },
    {
        "name": "Nostalgique",
        "description": "Jouer 5 parties en mode Génération",
        "condition_type": "games_by_mode",
        "condition_value": 5,
        "condition_extra": "generation",
        "points": 25,
    },
    {
        "name": "Karaokiste",
        "description": "Jouer une partie en mode Karaoké",
        "condition_type": "games_by_mode",
        "condition_value": 1,
        "condition_extra": "karaoke",
        "points": 20,
    },
    {
        "name": "Maître des paroles",
        "description": "Remporter une victoire en mode Paroles",
        "condition_type": "wins_by_mode",
        "condition_value": 1,
        "condition_extra": "paroles",
        "points": 50,
    },
    {
        "name": "Polyvalent",
        "description": "Jouer au moins une partie dans chacun des 5 modes",
        "condition_type": "all_modes_played",
        "condition_value": 5,
        "points": 100,
    },
    # Social
    {
        "name": "Sociable",
        "description": "Avoir 5 amis acceptés",
        "condition_type": "friends_count",
        "condition_value": 5,
        "points": 25,
    },
    {
        "name": "Hôte généreux",
        "description": "Héberger 10 parties terminées",
        "condition_type": "games_hosted",
        "condition_value": 10,
        "points": 40,
    },
    {
        "name": "L'inviteur",
        "description": "Envoyer 10 invitations de jeu",
        "condition_type": "invitations_sent",
        "condition_value": 10,
        "points": 30,
    },
    # Shop
    {
        "name": "Premier achat",
        "description": "Acheter un premier article dans la boutique",
        "condition_type": "items_purchased",
        "condition_value": 1,
        "points": 20,
    },
    {
        "name": "Collectionneur",
        "description": "Posséder 5 articles différents dans la boutique",
        "condition_type": "items_purchased",
        "condition_value": 5,
        "points": 60,
    },
    {
        "name": "Stratège",
        "description": "Utiliser le bonus Vol de points une fois",
        "condition_type": "bonus_used",
        "condition_value": 1,
        "condition_extra": "steal",
        "points": 40,
    },
    {
        "name": "Bouclier de fer",
        "description": "Utiliser le bonus Bouclier 5 fois",
        "condition_type": "bonus_used",
        "condition_value": 5,
        "condition_extra": "shield",
        "points": 40,
    },
    {
        "name": "Maître du temps",
        "description": "Utiliser le bonus Temps bonus 5 fois",
        "condition_type": "bonus_used",
        "condition_value": 5,
        "condition_extra": "time_bonus",
        "points": 35,
    },
    {
        "name": "Double ou rien",
        "description": "Utiliser le bonus Points doublés 10 fois",
        "condition_type": "bonus_used",
        "condition_value": 10,
        "condition_extra": "double_points",
        "points": 50,
    },
    {
        "name": "Maître du brouillard",
        "description": "Utiliser le bonus Mode Brouillard 3 fois",
        "condition_type": "bonus_used",
        "condition_value": 3,
        "condition_extra": "fog",
        "points": 45,
    },
    {
        "name": "Imposteur",
        "description": "Utiliser le bonus Joker 5 fois",
        "condition_type": "bonus_used",
        "condition_value": 5,
        "condition_extra": "joker",
        "points": 50,
    },
    {
        "name": "Maestro des bonus",
        "description": "Utiliser chacun des 8 types de bonus au moins une fois",
        "condition_type": "all_bonuses_used",
        "condition_value": 8,
        "points": 75,
    },
    # Performance avancée
    {
        "name": "En feu",
        "description": "Enchaîner 8 bonnes réponses consécutives dans une même partie",
        "condition_type": "in_game_streak",
        "condition_value": 8,
        "points": 75,
    },
    {
        "name": "Dominant",
        "description": "Remporter une victoire avec le double du score du 2ème joueur",
        "condition_type": "dominant_win",
        "condition_value": 1,
        "points": 100,
    },
]


class Command(BaseCommand):
    """Command to seed default achievements into the database."""

    help = "Seed default achievements into the database"

    def add_arguments(self, parser):
        """Add optional argument to reset achievements before seeding."""
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing achievements before seeding",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Update existing achievements (description, points, condition)",
        )

    def handle(self, *args, **options):
        """Seed achievements, optionally resetting existing ones first."""
        if options["reset"]:
            count = Achievement.objects.count()
            Achievement.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f"Deleted {count} existing achievements")
            )

        created_count = 0
        skipped_count = 0

        force = options["force"]
        updated_count = 0

        for data in DEFAULT_ACHIEVEMENTS:
            obj, created = Achievement.objects.get_or_create(
                name=data["name"],
                defaults=data,
            )
            if created:
                created_count += 1
            elif force:
                for field, value in data.items():
                    if field != "name":
                        setattr(obj, field, value)
                obj.save()
                updated_count += 1
                self.stdout.write(self.style.WARNING(f"  ↻ Mis à jour : {obj.name}"))
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded achievements: {created_count} created, "
                f"{updated_count} updated, "
                f"{skipped_count} already existed"
            )
        )
