"""
User models for InstantMusic.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom user model with additional fields."""
    
    email = models.EmailField(_('email address'), unique=True)
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/',
        null=True,
        blank=True,
        help_text=_('Photo de profil de l\'utilisateur')
    )
    bio = models.TextField(
        _('biographie'),
        max_length=500,
        blank=True,
        help_text=_('Description du profil utilisateur')
    )
    
    # Statistiques
    total_games_played = models.IntegerField(_('parties jouées'), default=0)
    total_wins = models.IntegerField(_('victoires'), default=0)
    total_points = models.IntegerField(_('points totaux'), default=0)
    
    # OAuth
    google_id = models.CharField(
        _('Google ID'),
        max_length=255,
        null=True,
        blank=True,
        unique=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)
    
    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        return self.username
    
    @property
    def win_rate(self) -> float:
        """Calcule le taux de victoire."""
        if self.total_games_played == 0:
            return 0.0
        return (self.total_wins / self.total_games_played) * 100
