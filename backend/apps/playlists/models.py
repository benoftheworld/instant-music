"""
Models for playlists (cached Spotify data).
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class Playlist(models.Model):
    """Cached Spotify playlist."""
    
    spotify_id = models.CharField(_('Spotify ID'), max_length=255, unique=True)
    name = models.CharField(_('nom'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    image_url = models.URLField(_('URL image'), blank=True)
    total_tracks = models.IntegerField(_('nombre de morceaux'), default=0)
    owner = models.CharField(_('propriétaire'), max_length=255, blank=True)
    external_url = models.URLField(_('lien Spotify'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('playlist')
        verbose_name_plural = _('playlists')
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return self.name


class Track(models.Model):
    """Cached Spotify track."""
    
    spotify_id = models.CharField(_('Spotify ID'), max_length=255, unique=True)
    name = models.CharField(_('titre'), max_length=255)
    artists = models.JSONField(_('artistes'), default=list)
    album = models.CharField(_('album'), max_length=255)
    album_image = models.URLField(_('image album'), blank=True)
    duration_ms = models.IntegerField(_('durée (ms)'))
    preview_url = models.URLField(_('aperçu audio'), blank=True, null=True)
    external_url = models.URLField(_('lien Spotify'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('morceau')
        verbose_name_plural = _('morceaux')
        ordering = ['name']
    
    def __str__(self) -> str:
        artists_str = ', '.join(self.artists) if self.artists else 'Unknown'
        return f"{self.name} - {artists_str}"


class SpotifyToken(models.Model):
    """OAuth 2.0 tokens for Spotify API access per user."""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='spotify_token',
        verbose_name=_('utilisateur')
    )
    access_token = models.TextField(_('access token'))
    refresh_token = models.TextField(_('refresh token'))
    token_type = models.CharField(_('type de token'), max_length=50, default='Bearer')
    expires_at = models.DateTimeField(_('expire le'))
    scope = models.TextField(_('scopes'), blank=True)
    
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('mis à jour le'), auto_now=True)
    
    class Meta:
        verbose_name = _('token Spotify')
        verbose_name_plural = _('tokens Spotify')
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return f"Spotify token for {self.user.username}"
    
    def is_expired(self) -> bool:
        """Check if the access token is expired."""
        return timezone.now() >= self.expires_at
    
    def is_expiring_soon(self, minutes: int = 5) -> bool:
        """Check if the token expires within the specified minutes."""
        from datetime import timedelta
        threshold = timezone.now() + timedelta(minutes=minutes)
        return self.expires_at <= threshold
