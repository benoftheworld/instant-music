# Generated migration — add karaoke_track JSON field to Game

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0014_add_karaoke_mode"),
    ]

    operations = [
        migrations.AddField(
            model_name="game",
            name="karaoke_track",
            field=models.JSONField(
                blank=True,
                default=None,
                help_text=(
                    "Informations du morceau sélectionné pour le karaoké "
                    "(youtube_video_id, track_name, artist_name, duration_ms)"
                ),
                null=True,
                verbose_name="morceau karaoké",
            ),
        ),
    ]
