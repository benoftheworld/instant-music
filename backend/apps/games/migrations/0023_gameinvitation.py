"""Migration: ajout du modèle GameInvitation."""

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("games", "0022_add_streak_bonus_to_gameanswer"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="GameInvitation",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("accepted", "Acceptée"),
                            ("declined", "Refusée"),
                            ("expired", "Expirée"),
                            ("cancelled", "Annulée"),
                        ],
                        default="pending",
                        max_length=20,
                        verbose_name="statut",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="créée le"),
                ),
                (
                    "expires_at",
                    models.DateTimeField(verbose_name="expire le"),
                ),
                (
                    "game",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="games.game",
                        verbose_name="partie",
                    ),
                ),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="received_game_invitations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="destinataire",
                    ),
                ),
                (
                    "sender",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sent_game_invitations",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="expéditeur",
                    ),
                ),
            ],
            options={
                "verbose_name": "invitation de partie",
                "verbose_name_plural": "invitations de partie",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="gameinvitation",
            constraint=models.UniqueConstraint(
                fields=["game", "recipient"],
                condition=models.Q(status="pending"),
                name="unique_pending_invitation_per_recipient",
            ),
        ),
    ]
