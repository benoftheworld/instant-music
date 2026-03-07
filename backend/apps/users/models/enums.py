"""Enums for the users app."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class FriendshipStatus(models.TextChoices):
    """Friendship request status."""

    PENDING = "pending", _("En attente")
    ACCEPTED = "accepted", _("Acceptée")
    REJECTED = "rejected", _("Refusée")


class TeamMemberRole(models.TextChoices):
    """Team member role."""

    OWNER = "owner", _("Propriétaire")
    ADMIN = "admin", _("Administrateur")
    MEMBER = "member", _("Membre")


class TeamJoinRequestStatus(models.TextChoices):
    """Team join request status."""

    PENDING = "pending", _("En attente")
    APPROVED = "approved", _("Approuvée")
    REJECTED = "rejected", _("Refusée")
