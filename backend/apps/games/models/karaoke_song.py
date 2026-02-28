"""
KaraokeSong model — catalogue of songs available for Karaoke mode.
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class KaraokeSong(models.Model):
    """
    Catalogue of songs available for Karaoke mode.
    Filled manually by admins. Associates a YouTube video with
    a LRCLib.net lyrics entry so synchronised lyrics are always
    resolved from the correct source.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_("titre"), max_length=255)
    artist = models.CharField(_("artiste"), max_length=255)
    youtube_video_id = models.CharField(
        _("ID vidéo YouTube"),
        max_length=20,
        unique=True,
        help_text=_("Identifiant de la vidéo YouTube (ex: dQw4w9WgXcQ)"),
    )
    lrclib_id = models.IntegerField(
        _("ID LRCLib"),
        null=True,
        blank=True,
        help_text=_(
            "ID numérique sur lrclib.net pour récupérer les paroles "
            "synchronisées directement (évite les recherches par nom)."
        ),
    )
    album_image_url = models.URLField(
        _("image album"), max_length=500, blank=True, default=""
    )
    duration_ms = models.IntegerField(
        _("durée (ms)"), default=0, help_text=_("Durée en millisecondes")
    )
    is_active = models.BooleanField(
        _("actif"),
        default=True,
        help_text=_("Seuls les morceaux actifs sont proposés aux joueurs"),
    )
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("mis à jour le"), auto_now=True)

    class Meta:
        verbose_name = _("morceau karaoké")
        verbose_name_plural = _("morceaux karaoké")
        ordering = ["artist", "title"]

    def __str__(self) -> str:
        return f"{self.artist} — {self.title}"
