"""
Models for achievements.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Achievement(models.Model):
    """Achievement model."""
    
    name = models.CharField(_('nom'), max_length=100)
    description = models.TextField(_('description'))
    icon = models.ImageField(_('icône'), upload_to='achievements/', null=True, blank=True)
    points = models.IntegerField(_('points'), default=10)
    
    # Conditions
    condition_type = models.CharField(_('type de condition'), max_length=50)
    condition_value = models.IntegerField(_('valeur de condition'))
    
    class Meta:
        verbose_name = _('succès')
        verbose_name_plural = _('succès')
    
    def __str__(self) -> str:
        return self.name


class UserAchievement(models.Model):
    """User's unlocked achievements."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE
    )
    unlocked_at = models.DateTimeField(_('débloqué le'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('succès utilisateur')
        verbose_name_plural = _('succès utilisateurs')
        unique_together = ['user', 'achievement']
    
    def __str__(self) -> str:
        return f"{self.user.username} - {self.achievement.name}"
