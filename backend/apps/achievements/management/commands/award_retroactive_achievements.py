"""Vérifier rétroactivement les succès des utilisateurs et les attribuer."""

from django.core.management.base import BaseCommand

from apps.achievements.services import achievement_service
from apps.games.models import GameAnswer, GamePlayer
from apps.users.models import User


class Command(BaseCommand):
    """Classe de commande pour vérifier les succès des utilisateurs.
    
    Cette commande parcourt tous les utilisateurs ayant joué au moins une 
    partie, vérifie s'ils remplissent les conditions de succès basés sur leurs 
    parties passées, et leur attribue les succès correspondants.
    """

    help = "Vérifier rétroactivement les succès des utilisateurs."

    def handle(self, *args, **options):
        """Parcourir les utilisateurs et vérifier leurs succès.
        
        Pour chaque utilisateur, la commande vérifie s'il a joué au moins une
        partie, puis vérifie s'il remplit les conditions de succès basés sur
        ses parties passées (par exemple, s'il a eu une partie parfaite). Si un
        succès est attribué, il affiche le nom de l'utilisateur et les succès
        attribués.
        
        À la fin, elle affiche le nombre total de succès attribués.
        
        Args:
            *args: Arguments positionnels (non utilisés).
            **options: Arguments nommés (non utilisés).
            
        Returns:
            None
        
        """
        users = User.objects.filter(total_games_played__gt=0)
        total_awarded = 0

        # Parcourir les utilisateurs et vérifier leurs succès
        for user in users:
            # Vérifier si l'utilisateur a déjà eu une partie parfaite
            perfect_game = False
            game_players = GamePlayer.objects.filter(
                user=user, rank__isnull=False
            )
            # Si l'utilisateur a joué au moins une partie, 
            # vérifier s'il a eu une partie parfaite
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
