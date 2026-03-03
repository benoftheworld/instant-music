"""
Service for checking and awarding achievements to users.
"""

import logging

from django.db import transaction

from .models import Achievement, UserAchievement

logger = logging.getLogger(__name__)


def _push_achievement_notification(user_id: int, achievement) -> None:
    """Push a WebSocket notification to the user for a newly unlocked achievement."""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        from django.conf import settings

        channel_layer = get_channel_layer()
        if channel_layer is None:
            return

        icon_url = None
        if achievement.icon:
            base_url = getattr(settings, "BACKEND_BASE_URL", "").rstrip("/")
            icon_url = f"{base_url}{achievement.icon.url}"

        async_to_sync(channel_layer.group_send)(
            f"notifications_{user_id}",
            {
                "type": "notify.achievement_unlocked",
                "achievement": {
                    "id": str(achievement.id),
                    "name": achievement.name,
                    "description": achievement.description,
                    "icon": icon_url,
                    "points": achievement.points,
                },
            },
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to push achievement WS notification: %s", exc)

# Achievement condition types
CONDITION_GAMES_PLAYED = "games_played"
CONDITION_WINS = "wins"
CONDITION_POINTS = "points"
CONDITION_PERFECT_ROUND = "perfect_round"
CONDITION_WIN_STREAK = "win_streak"


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
            UserAchievement.objects.filter(user=user).values_list(
                "achievement_id", flat=True
            )
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
                    achievement.name,
                    user.username,
                )

                # Créditer les pièces de la boutique
                if achievement.points > 0:
                    user.coins_balance = (
                        user.__class__.objects.filter(pk=user.pk)
                        .values_list("coins_balance", flat=True)
                        .first()
                        or 0
                    ) + achievement.points
                    user.__class__.objects.filter(pk=user.pk).update(
                        coins_balance=user.coins_balance
                    )
                    logger.info(
                        "Credited %d coins to user '%s' (achievement: %s)",
                        achievement.points,
                        user.username,
                        achievement.name,
                    )

                _push_achievement_notification(user.id, achievement)

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
            if round_data and round_data.get("perfect_game"):
                return True
            return False

        elif ctype == CONDITION_WIN_STREAK:
            # Check consecutive wins from recent games
            from apps.games.models import GamePlayer

            recent_games = GamePlayer.objects.filter(user=user).order_by(
                "-joined_at"
            )[:cvalue]

            if recent_games.count() < cvalue:
                return False

            return all(p.rank == 1 for p in recent_games)

        else:
            logger.warning("Unknown achievement condition type: %s", ctype)
            return False


# Singleton
achievement_service = AchievementService()
