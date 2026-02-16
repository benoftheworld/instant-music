"""
Models for playlists (cached YouTube data).
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Playlist(models.Model):
    """Cached YouTube playlist."""
    
    youtube_id = models.CharField(_('YouTube ID'), max_length=255, unique=True)
    name = models.CharField(_('nom'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    image_url = models.URLField(_('URL image'), blank=True)
    total_tracks = models.IntegerField(_('nombre de morceaux'), default=0)
    owner = models.CharField(_('propriétaire'), max_length=255, blank=True)
    external_url = models.URLField(_('lien YouTube'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('playlist')
        verbose_name_plural = _('playlists')
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return self.name


class Track(models.Model):
    """Cached YouTube track/video."""
    
    youtube_id = models.CharField(_('YouTube ID'), max_length=255, unique=True)
    name = models.CharField(_('titre'), max_length=255)
    artists = models.JSONField(_('artistes'), default=list)
    album = models.CharField(_('album/chaîne'), max_length=255)
    album_image = models.URLField(_('image'), blank=True)
    duration_ms = models.IntegerField(_('durée (ms)'))
    preview_url = models.URLField(_('URL vidéo'), blank=True, null=True)
    external_url = models.URLField(_('lien YouTube'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('morceau')
        verbose_name_plural = _('morceaux')
        ordering = ['name']
    
    def __str__(self) -> str:
        artists_str = ', '.join(self.artists) if self.artists else 'Unknown'
        return f"{self.name} - {artists_str}"
