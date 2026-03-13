# Migration: ajout du mode "mollo" (manipulation audio - ralenti).

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("games", "0025_game_status_is_public_db_index"),
    ]

    operations = [
        migrations.AlterField(
            model_name="game",
            name="mode",
            field=models.CharField(
                choices=[
                    ("classique", "Classique"),
                    ("rapide", "Rapide"),
                    ("generation", "Génération"),
                    ("paroles", "Paroles"),
                    ("karaoke", "Karaoké"),
                    ("mollo", "Mollo (ralenti)"),
                ],
                default="classique",
                max_length=20,
                verbose_name="mode de jeu",
            ),
        ),
    ]
