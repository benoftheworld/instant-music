"""Custom User model sans first_name/last_name, avec email chiffré."""

import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.users.encryption import hash_email
from apps.users.fields import EncryptedEmailField


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError("The Username must be set")
        if not email:
            raise ValueError("The Email must be set")
        # Normalise l'email (minuscules domaine + local)
        email = self.normalize_email(email).lower()
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, password, **extra_fields)

    def get_by_email(self, email: str) -> "User":
        """Recherche un utilisateur par email en clair via le hash HMAC."""
        return self.get(email_hash=hash_email(email))


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model sans first_name/last_name, email chiffré au repos."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(_("username"), max_length=150, unique=True)

    # Email chiffré (Fernet AES) — le champ Python retourne l'email en clair
    email = EncryptedEmailField(_("email address"))
    # HMAC-SHA256 de l'email normalisé — utilisé pour les lookups ORM et l'unicité
    email_hash = models.CharField(
        _("email hash"),
        max_length=64,
        unique=True,
        db_index=True,
        editable=False,
    )

    avatar = models.ImageField(
        _("avatar"),
        upload_to="avatars/",
        null=True,
        blank=True,
        help_text=_("Photo de profil de l'utilisateur"),
    )

    # Statistiques
    total_games_played = models.IntegerField(_("parties jouées"), default=0)
    total_wins = models.IntegerField(_("victoires"), default=0)
    total_points = models.IntegerField(_("points totaux"), default=0)

    # Boutique — pièces gagnées grâce aux achievements
    coins_balance = models.IntegerField(
        _("solde de pièces"),
        default=0,
        help_text=_(
            "Pièces accumulées via les achievements, utilisables dans la boutique"
        ),
    )

    # OAuth
    google_id = models.CharField(
        _("Google ID"),
        max_length=255,
        null=True,
        blank=True,
        unique=True,
    )

    # Permissions / status
    is_active = models.BooleanField(_("active"), default=True)
    is_staff = models.BooleanField(_("staff status"), default=False)
    # RGPD — consentement
    privacy_policy_accepted_at = models.DateTimeField(
        _(\"politique de confidentialité acceptée le\"),
        null=True,
        blank=True,
        help_text=_(\"Date d'acceptation de la politique de confidentialité.\"),
    )
    # Timestamps
    created_at = models.DateTimeField(_("créé le"), auto_now_add=True)
    updated_at = models.DateTimeField(_("modifié le"), auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = _("utilisateur")
        verbose_name_plural = _("utilisateurs")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.username

    def save(self, *args, **kwargs):
        """Calcule automatiquement le hash de l'email avant chaque sauvegarde."""
        if self.email:
            # Normalise en minuscules (cohérence avec encrypt_email/hash_email)
            if isinstance(self.email, str):
                self.email = self.email.lower()
            self.email_hash = hash_email(self.email)
        super().save(*args, **kwargs)

    @property
    def win_rate(self) -> float:
        if self.total_games_played == 0:
            return 0.0
        return (self.total_wins / self.total_games_played) * 100
