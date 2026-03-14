"""Tâches Celery de maintenance RGPD.

Nettoyage périodique des données expirées pour respecter la rétention minimale.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(
    name="rgpd.purge_expired_invitations",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def purge_expired_invitations(self):
    """Supprime les invitations de jeu expirées depuis plus de 7 jours."""
    from apps.games.models.game_invitation import GameInvitation

    try:
        cutoff = timezone.now() - timedelta(days=7)
        deleted, _ = GameInvitation.objects.filter(expires_at__lt=cutoff).delete()
        if deleted:
            logger.info("purge_expired_invitations: %d invitations supprimées", deleted)
        return deleted
    except Exception as exc:
        logger.exception("purge_expired_invitations failed")
        raise self.retry(exc=exc)  # noqa: B904


@shared_task(
    name="rgpd.anonymize_old_game_data",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def anonymize_old_game_data(self, retention_days: int = 365):
    """Anonymise les données de jeu plus anciennes que `retention_days` jours.

    Les parties sont conservées pour les statistiques globales mais les
    réponses individuelles sont supprimées et les joueurs anonymisés.
    """
    from apps.games.models import Game, GameAnswer

    cutoff = timezone.now() - timedelta(days=retention_days)

    # Supprime les réponses individuelles des parties anciennes terminées (en chunks)
    old_answers_qs = GameAnswer.objects.filter(
        round__game__finished_at__lt=cutoff,
        round__game__status="finished",
    )
    deleted_count = 0
    while True:
        batch_ids = list(old_answers_qs.values_list("id", flat=True)[:1000])
        if not batch_ids:
            break
        count, _ = GameAnswer.objects.filter(id__in=batch_ids).delete()
        deleted_count += count

    if deleted_count:
        logger.info(
            "anonymize_old_game_data: %d réponses supprimées (rétention=%d jours)",
            deleted_count,
            retention_days,
        )

    # Marque les anciennes parties annulées pour suppression
    old_cancelled = Game.objects.filter(status="cancelled", created_at__lt=cutoff)
    deleted_cancelled, _ = old_cancelled.delete()

    if deleted_cancelled:
        logger.info(
            "anonymize_old_game_data: %d parties annulées supprimées",
            deleted_cancelled,
        )

    return {
        "answers_deleted": deleted_count,
        "cancelled_games_deleted": deleted_cancelled,
    }
