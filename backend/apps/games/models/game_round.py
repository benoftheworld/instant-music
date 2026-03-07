"""GameRound model — round in a game.
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from .game import Game


class GameRound(models.Model):
    """Round in a game."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="rounds",
        verbose_name=_("partie"),
    )
    round_number = models.IntegerField(_("numéro du round"))
    track_id = models.CharField(_("ID du morceau"), max_length=255)
    track_name = models.CharField(_("nom du morceau"), max_length=255)
    artist_name = models.CharField(_("nom de l'artiste"), max_length=255)
    correct_answer = models.CharField(_("bonne réponse"), max_length=255)
    options = models.JSONField(_("options"), default=list)
    preview_url = models.URLField(
        _("URL preview audio"),
        max_length=500,
        blank=True,
        default="",
    )
    question_type = models.CharField(
        _("type de question"),
        max_length=30,
        default="guess_title",
    )
    question_text = models.CharField(
        _("texte de la question"),
        max_length=500,
        default="Quel est le titre de ce morceau ?",
    )
    extra_data = models.JSONField(
        _("données supplémentaires"),
        default=dict,
        blank=True,
    )
    duration = models.IntegerField(_("durée (secondes)"), default=30)

    started_at = models.DateTimeField(_("démarré le"), null=True, blank=True)
    ended_at = models.DateTimeField(_("terminé le"), null=True, blank=True)

    class Meta:
        verbose_name = _("round")
        verbose_name_plural = _("rounds")
        unique_together = ["game", "round_number"]
        ordering = ["game", "round_number"]

    def __str__(self) -> str:
        return f"Round {self.round_number} - {self.game.room_code}"
