"""
Models for playlists (cached Spotify data).
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Playlist(models.Model):
    """Cached Spotify playlist."""
    
    spotify_id = models.CharField(_('Spotify ID'), max_length=255, unique=True)
    name = models.CharField(_('nom'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    image_url = models.URLField(_('URL image'), blank=True)
    total_tracks = models.IntegerField(_('nombre de morceaux'), default=0)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('playlist')
        verbose_name_plural = _('playlists')
    
    def __str__(self) -> str:
        return self.name
