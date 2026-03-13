"""Migration: add bonuses_enabled field to Game."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("games", "0028_game_is_party_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="bonuses_enabled",
            field=models.BooleanField(
                default=True,
                help_text="Si désactivé, les joueurs ne peuvent pas utiliser de bonus pendant la partie",
                verbose_name="bonus activés",
            ),
        ),
    ]
