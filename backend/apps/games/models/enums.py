"""Enums / TextChoices for the games app.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class GameMode(models.TextChoices):
    """Game mode choices."""

    CLASSIQUE = "classique", _("Classique")
    RAPIDE = "rapide", _("Rapide")
    GENERATION = "generation", _("Génération")
    PAROLES = "paroles", _("Paroles")
    KARAOKE = "karaoke", _("Karaoké")
    LENT = "mollo", _("Lent (ralenti)")
    INVERSE = "inverse", _("À l'envers")


class AnswerMode(models.TextChoices):
    """Answer mode choices."""

    MCQ = "mcq", _("QCM")
    TEXT = "text", _("Saisie libre")


class GuessTarget(models.TextChoices):
    """What the player must guess in MCQ mode for Classique/Rapide."""

    ARTIST = "artist", _("Artiste")
    TITLE = "title", _("Titre")


class GameStatus(models.TextChoices):
    """Game status choices."""

    WAITING = "waiting", _("En attente")
    IN_PROGRESS = "in_progress", _("En cours")
    FINISHED = "finished", _("Terminée")
    CANCELLED = "cancelled", _("Annulée")
