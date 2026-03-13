# Migration: ajout d'index DB sur Game.status et Game.is_public.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("games", "0024_remove_gameinvitation_unique_pending_invitation_per_recipient_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="game",
            name="status",
            field=models.CharField(
                choices=[
                    ("waiting", "En attente"),
                    ("in_progress", "En cours"),
                    ("finished", "Terminée"),
                    ("cancelled", "Annulée"),
                ],
                db_index=True,
                default="waiting",
                max_length=20,
                verbose_name="statut",
            ),
        ),
        migrations.AlterField(
            model_name="game",
            name="is_public",
            field=models.BooleanField(
                db_index=True,
                default=False,
                help_text="Si activé, la partie apparaît dans la liste des parties publiques",
                verbose_name="partie publique",
            ),
        ),
    ]
