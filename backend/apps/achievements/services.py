"""
Service for checking and awarding achievements to users.
"""
import logging
from django.db import transaction
from .models import Achievement, UserAchievement

logger = logging.getLogger(__name__)


# Achievement condition types
CONDITION_GAMES_PLAYED = 'games_played'
CONDITION_WINS = 'wins'
CONDITION_POINTS = 'points'
CONDITION_PERFECT_ROUND = 'perfect_round'
CONDITION_WIN_STREAK = 'win_streak'


class AchievementService:
    """Service to check and award achievements."""
    
    @transaction.atomic
    def check_and_award(self, user, game=None, round_data=None):
        """
        Check all achievements for a user and award any newly earned ones.
        
        Args:
            user: The user to check achievements for
            game: Optional game that just finished (for context)
            round_data: Optional dict with round-specific info (e.g. perfect_round=True)
        
        Returns:
            List of newly awarded Achievement objects
        """
        achievements = Achievement.objects.all()
        already_unlocked = set(
            UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        )
        
        newly_awarded = []
        
        for achievement in achievements:
            if achievement.id in already_unlocked:
                continue
            
            if self._check_condition(user, achievement, game, round_data):
                UserAchievement.objects.create(
                    user=user,
                    achievement=achievement,
                )
                newly_awarded.append(achievement)
                logger.info(
                    "Achievement '%s' awarded to user '%s'",
                    achievement.name, user.username
                )
        
        return newly_awarded
    
    def _check_condition(self, user, achievement, game=None, round_data=None):
        """Check if a user meets the condition for an achievement."""
        ctype = achievement.condition_type
        cvalue = achievement.condition_value
        
        if ctype == CONDITION_GAMES_PLAYED:
            return user.total_games_played >= cvalue
        
        elif ctype == CONDITION_WINS:
            return user.total_wins >= cvalue
        
        elif ctype == CONDITION_POINTS:
            return user.total_points >= cvalue
        
        elif ctype == CONDITION_PERFECT_ROUND:
            # Perfect round: all answers correct in a single game
            if round_data and round_data.get('perfect_game'):
                return True
            return False
        
        elif ctype == CONDITION_WIN_STREAK:
            # Check consecutive wins from recent games
            from apps.games.models import GamePlayer
            recent_games = GamePlayer.objects.filter(
                user=user
            ).order_by('-joined_at')[:cvalue]
            
            if recent_games.count() < cvalue:
                return False
            
            return all(p.rank == 1 for p in recent_games)
        
        else:
            logger.warning("Unknown achievement condition type: %s", ctype)
            return False


# Singleton
achievement_service = AchievementService()
