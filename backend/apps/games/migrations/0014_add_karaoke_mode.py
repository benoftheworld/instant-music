# Generated migration — add karaoke game mode

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0013_new_game_modes"),
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
                ],
                default="classique",
                max_length=20,
                verbose_name="mode de jeu",
            ),
        ),
    ]
