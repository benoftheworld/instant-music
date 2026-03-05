"""Tâches Celery pour le système d'achievements.
"""

import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="achievements.check_and_award",
    bind=True,
    max_retries=3,
    default_retry_delay=10,
)
def check_achievements_async(self, user_id, game_id=None, round_data=None):
    """Vérifie et attribue les achievements de manière asynchrone."""
    from apps.achievements.services import achievement_service
    from apps.games.models import Game
    from apps.users.models import User

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("check_achievements_async: user %s not found", user_id)
        return

    game = None
    if game_id:
        try:
            game = Game.objects.get(pk=game_id)
        except Game.DoesNotExist:
            logger.warning("check_achievements_async: game %s not found", game_id)

    achievement_service.check_and_award(user, game=game, round_data=round_data)
