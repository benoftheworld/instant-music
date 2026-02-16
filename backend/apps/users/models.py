"""
Custom User model without first_name/last_name.
Switch from AbstractUser to AbstractBaseUser so the database no longer contains
the `first_name` and `last_name` fields for our custom `User` model.
"""
from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    BaseUserManager,
)
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username must be set')
        if not email:
            raise ValueError('The Email must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model without first_name/last_name."""

    username = models.CharField(_('username'), max_length=150, unique=True)
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

    # Permissions / status
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff status'), default=False)

    # Timestamps
    created_at = models.DateTimeField(_('créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('modifié le'), auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.username

    @property
    def win_rate(self) -> float:
        if self.total_games_played == 0:
            return 0.0
        return (self.total_wins / self.total_games_played) * 100
