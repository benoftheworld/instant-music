"""
Service for checking and awarding achievements to users.
"""

import logging
from typing import Any

from django.db import transaction

from .models import Achievement, UserAchievement

logger = logging.getLogger(__name__)


def _push_achievement_notification(user_id: int, achievement: "Achievement") -> None:
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


# Achievement condition types — existants
CONDITION_GAMES_PLAYED = "games_played"
CONDITION_WINS = "wins"
CONDITION_POINTS = "points"
CONDITION_PERFECT_ROUND = "perfect_round"
CONDITION_WIN_STREAK = "win_streak"
# Vitesse
CONDITION_FAST_ANSWERS = "fast_answers"
CONDITION_ALL_FAST_ROUND = "all_fast_round"
# Précision
CONDITION_ACCURACY = "accuracy"
CONDITION_GLOBAL_STREAK = "global_correct_streak"
CONDITION_SINGLE_GAME_SCORE = "single_game_score"
# Modes de jeu
CONDITION_GAMES_BY_MODE = "games_by_mode"
CONDITION_WINS_BY_MODE = "wins_by_mode"
CONDITION_ALL_MODES_PLAYED = "all_modes_played"
# Social
CONDITION_FRIENDS_COUNT = "friends_count"
CONDITION_GAMES_HOSTED = "games_hosted"
CONDITION_INVITATIONS_SENT = "invitations_sent"
# Shop / bonus
CONDITION_ITEMS_PURCHASED = "items_purchased"
CONDITION_BONUS_USED = "bonus_used"
CONDITION_ALL_BONUSES_USED = "all_bonuses_used"
# Performance avancée
CONDITION_IN_GAME_STREAK = "in_game_streak"
CONDITION_DOMINANT_WIN = "dominant_win"


class AchievementService:
    """Service to check and award achievements."""

    @transaction.atomic
    def check_and_award(
        self,
        user: Any,
        game: Any = None,
        round_data: dict[str, Any] | None = None,
    ) -> list["Achievement"]:
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

    def _check_condition(
        self,
        user: Any,
        achievement: Achievement,
        game: Any = None,
        round_data: dict[str, Any] | None = None,
    ) -> bool:
        """Check if a user meets the condition for an achievement."""
        ctype = achievement.condition_type
        cvalue = achievement.condition_value
        cextra = achievement.condition_extra

        if ctype == CONDITION_GAMES_PLAYED:
            return user.total_games_played >= cvalue  # type: ignore[no-any-return]

        elif ctype == CONDITION_WINS:
            return user.total_wins >= cvalue  # type: ignore[no-any-return]

        elif ctype == CONDITION_POINTS:
            return user.total_points >= cvalue  # type: ignore[no-any-return]

        elif ctype == CONDITION_PERFECT_ROUND:
            # Perfect round: all answers correct in a single game
            if round_data and round_data.get("perfect_game"):
                return True
            return False

        elif ctype == CONDITION_WIN_STREAK:
            # Check consecutive wins from recent games
            from apps.games.models import GamePlayer

            recent_games = GamePlayer.objects.filter(user=user).order_by("-joined_at")[
                :cvalue
            ]

            if recent_games.count() < cvalue:
                return False

            return all(p.rank == 1 for p in recent_games)

        elif ctype == CONDITION_FAST_ANSWERS:
            # Nombre de bonnes réponses en moins de N secondes (cextra = seuil)
            from apps.games.models import GameAnswer

            threshold = float(cextra) if cextra else 5.0
            count = GameAnswer.objects.filter(
                player__user=user, is_correct=True, response_time__lt=threshold
            ).count()
            return count >= cvalue  # type: ignore[no-any-return]

        elif ctype == CONDITION_ALL_FAST_ROUND:
            # Partie parfaite avec toutes les réponses sous N secondes
            if not (round_data and round_data.get("perfect_game")):
                return False
            max_rt = round_data.get("max_response_time", 999.0)
            threshold = float(cextra) if cextra else 2.0
            return max_rt < threshold  # type: ignore[no-any-return]

        elif ctype == CONDITION_ACCURACY:
            # Précision globale >= cvalue% sur au moins cextra parties
            from apps.games.models import GameAnswer

            min_games = int(cextra) if cextra else 20
            if user.total_games_played < min_games:
                return False
            total = GameAnswer.objects.filter(player__user=user).count()
            if total == 0:
                return False
            correct = GameAnswer.objects.filter(
                player__user=user, is_correct=True
            ).count()
            return (correct / total * 100) >= cvalue  # type: ignore[no-any-return]

        elif ctype == CONDITION_GLOBAL_STREAK:
            # Streak max de bonnes réponses consécutives dans une même partie
            if round_data:
                return round_data.get("max_streak", 0) >= cvalue  # type: ignore[no-any-return]
            # Fallback : cherche dans tout l'historique
            from apps.games.models import GameAnswer, GamePlayer

            player_ids = list(
                GamePlayer.objects.filter(user=user).values_list("id", flat=True)
            )
            for pid in player_ids:
                answers = list(
                    GameAnswer.objects.filter(player_id=pid)
                    .order_by("round__round_number")
                    .values_list("is_correct", flat=True)
                )
                current = 0
                for correct in answers:
                    if correct:
                        current += 1
                        if current >= cvalue:
                            return True
                    else:
                        current = 0
            return False

        elif ctype == CONDITION_SINGLE_GAME_SCORE:
            from apps.games.models import GamePlayer

            return GamePlayer.objects.filter(  # type: ignore[no-any-return]
                user=user, score__gte=cvalue
            ).exists()

        elif ctype == CONDITION_GAMES_BY_MODE:
            from apps.games.models import GamePlayer

            return (  # type: ignore[no-any-return]
                GamePlayer.objects.filter(
                    user=user, game__mode=cextra, game__status="finished"
                ).count()
                >= cvalue
            )

        elif ctype == CONDITION_WINS_BY_MODE:
            from apps.games.models import GamePlayer

            return (  # type: ignore[no-any-return]
                GamePlayer.objects.filter(user=user, game__mode=cextra, rank=1).count()
                >= cvalue
            )

        elif ctype == CONDITION_ALL_MODES_PLAYED:
            from apps.games.models import GamePlayer

            played_modes = (
                GamePlayer.objects.filter(user=user, game__status="finished")
                .values_list("game__mode", flat=True)
                .distinct()
                .count()
            )
            return played_modes >= cvalue  # type: ignore[no-any-return]

        elif ctype == CONDITION_FRIENDS_COUNT:
            from django.db.models import Q

            from apps.users.models import Friendship

            count = Friendship.objects.filter(
                Q(from_user=user) | Q(to_user=user), status="accepted"
            ).count()
            return count >= cvalue  # type: ignore[no-any-return]

        elif ctype == CONDITION_GAMES_HOSTED:
            from apps.games.models import Game

            return (  # type: ignore[no-any-return]
                Game.objects.filter(host=user, status="finished").count() >= cvalue
            )

        elif ctype == CONDITION_INVITATIONS_SENT:
            from apps.games.models import GameInvitation

            return GameInvitation.objects.filter(sender=user).count() >= cvalue  # type: ignore[no-any-return]

        elif ctype == CONDITION_ITEMS_PURCHASED:
            from apps.shop.models import UserInventory

            distinct_items = (
                UserInventory.objects.filter(user=user)
                .values("item")
                .distinct()
                .count()
            )
            return distinct_items >= cvalue  # type: ignore[no-any-return]

        elif ctype == CONDITION_BONUS_USED:
            from apps.shop.models import GameBonus

            return (  # type: ignore[no-any-return]
                GameBonus.objects.filter(
                    player__user=user, bonus_type=cextra, is_used=True
                ).count()
                >= cvalue
            )

        elif ctype == CONDITION_ALL_BONUSES_USED:
            from apps.shop.models import BonusType, GameBonus

            for btype in BonusType.values:
                used = GameBonus.objects.filter(
                    player__user=user, bonus_type=btype, is_used=True
                ).exists()
                if not used:
                    return False
            return True

        elif ctype == CONDITION_IN_GAME_STREAK:
            if round_data:
                return round_data.get("max_streak", 0) >= cvalue  # type: ignore[no-any-return]
            return False

        elif ctype == CONDITION_DOMINANT_WIN:
            if round_data:
                return round_data.get("dominant_win", False)  # type: ignore[no-any-return]
            return False

        else:
            logger.warning("Unknown achievement condition type: %s", ctype)
            return False


# Singleton
achievement_service = AchievementService()
