"""
Models for games.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid


class GameMode(models.TextChoices):
    """Game mode choices."""

    CLASSIQUE = "classique", _("Classique")
    RAPIDE = "rapide", _("Rapide")
    GENERATION = "generation", _("Génération")
    PAROLES = "paroles", _("Paroles")
    KARAOKE = "karaoke", _("Karaoké")


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


class Game(models.Model):
    """Game model representing a game session."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        _("nom de la partie"),
        max_length=100,
        blank=True,
        help_text=_("Nom optionnel pour identifier la partie"),
    )
    room_code = models.CharField(
        _("code de la salle"),
        max_length=6,
        unique=True,
        help_text=_("Code unique pour rejoindre la partie"),
    )
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="hosted_games",
        verbose_name=_("hôte"),
    )
    mode = models.CharField(
        _("mode de jeu"),
        max_length=20,
        choices=GameMode.choices,
        default=GameMode.CLASSIQUE,
    )
    guess_target = models.CharField(
        _("cible à deviner"),
        max_length=10,
        choices=GuessTarget.choices,
        default=GuessTarget.TITLE,
        help_text=_(
            "En mode QCM Classique/Rapide : deviner l'artiste ou le titre"
        ),
    )
    status = models.CharField(
        _("statut"),
        max_length=20,
        choices=GameStatus.choices,
        default=GameStatus.WAITING,
    )
    max_players = models.IntegerField(_("nombre max de joueurs"), default=8)
    num_rounds = models.IntegerField(_("nombre de rounds"), default=10)
    playlist_id = models.CharField(
        _("ID playlist Deezer"), max_length=255, null=True, blank=True
    )
    is_online = models.BooleanField(_("en ligne"), default=True)
    answer_mode = models.CharField(
        _("mode de réponse"),
        max_length=10,
        choices=AnswerMode.choices,
        default=AnswerMode.MCQ,
        help_text=_("QCM ou saisie libre"),
    )
    round_duration = models.IntegerField(
        _("durée d'un round (secondes)"),
        default=30,
        help_text=_("Durée en secondes de chaque round (10-60)"),
    )
    timer_start_round = models.IntegerField(
        _("timer début de round (secondes)"),
        default=5,
        help_text=_("Compte à rebours avant le début du round (3-15)"),
    )
    score_display_duration = models.IntegerField(
        _("temps affichage score (secondes)"),
        default=10,
        help_text=_("Durée d'affichage du score en fin de round (3-30)"),
    )
    lyrics_words_count = models.IntegerField(
        _("nombre de mots à deviner (paroles)"),
        default=3,
        help_text=_("Nombre de mots à deviner dans le mode Paroles (2-10)"),
    )

    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)
    started_at = models.DateTimeField(_("démarré le"), null=True, blank=True)
    finished_at = models.DateTimeField(_("terminé le"), null=True, blank=True)

    class Meta:
        verbose_name = _("partie")
        verbose_name_plural = _("parties")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Game {self.room_code} - {self.get_mode_display()}"


class GamePlayer(models.Model):
    """Players in a game."""

    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name="players",
        verbose_name=_("partie"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_participations",
        verbose_name=_("joueur"),
    )
    score = models.IntegerField(_("score"), default=0)
    rank = models.IntegerField(_("classement"), null=True, blank=True)
    is_connected = models.BooleanField(_("connecté"), default=True)
    joined_at = models.DateTimeField(_("a rejoint le"), auto_now_add=True)

    class Meta:
        verbose_name = _("joueur de partie")
        verbose_name_plural = _("joueurs de partie")
        unique_together = ["game", "user"]
        ordering = ["-score"]

    def __str__(self) -> str:
        return f"{self.user.username} - {self.game.room_code}"


class GameRound(models.Model):
    """Round in a game."""

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


class GameAnswer(models.Model):
    """Player's answer in a round."""

    round = models.ForeignKey(
        GameRound,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("round"),
    )
    player = models.ForeignKey(
        GamePlayer,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name=_("joueur"),
    )
    answer = models.CharField(_("réponse"), max_length=255)
    is_correct = models.BooleanField(_("correct"), default=False)
    points_earned = models.IntegerField(_("points gagnés"), default=0)
    response_time = models.FloatField(_("temps de réponse (secondes)"))
    answered_at = models.DateTimeField(_("répondu le"), auto_now_add=True)

    class Meta:
        verbose_name = _("réponse")
        verbose_name_plural = _("réponses")
        unique_together = ["round", "player"]

    def __str__(self) -> str:
        return f"{self.player.user.username} - Round {self.round.round_number}"
