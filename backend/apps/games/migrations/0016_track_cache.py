# Generated migration — adds TrackCache model

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("games", "0015_game_karaoke_track"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrackCache",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "artist_key",
                    models.CharField(
                        db_index=True,
                        help_text="Artiste normalisé (minuscules, sans suffixes)",
                        max_length=255,
                        verbose_name="clé artiste",
                    ),
                ),
                (
                    "track_key",
                    models.CharField(
                        db_index=True,
                        help_text="Titre normalisé (minuscules, sans suffixes)",
                        max_length=255,
                        verbose_name="clé titre",
                    ),
                ),
                (
                    "artist_name",
                    models.CharField(max_length=255, verbose_name="artiste"),
                ),
                (
                    "track_name",
                    models.CharField(max_length=255, verbose_name="titre"),
                ),
                (
                    "youtube_video_id",
                    models.CharField(
                        blank=True,
                        default="",
                        max_length=20,
                        verbose_name="ID vidéo YouTube",
                    ),
                ),
                (
                    "video_duration_ms",
                    models.IntegerField(
                        default=0, verbose_name="durée vidéo (ms)"
                    ),
                ),
                (
                    "album_image",
                    models.URLField(
                        blank=True,
                        default="",
                        max_length=500,
                        verbose_name="image album",
                    ),
                ),
                (
                    "synced_lyrics",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text='Liste de {"time_ms": int, "text": str}',
                        verbose_name="paroles synchronisées",
                    ),
                ),
                (
                    "plain_lyrics",
                    models.TextField(
                        blank=True,
                        default="",
                        verbose_name="paroles brutes",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="créé le"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="mis à jour le"
                    ),
                ),
            ],
            options={
                "verbose_name": "cache de piste",
                "verbose_name_plural": "cache de pistes",
                "ordering": ["-updated_at"],
            },
        ),
        migrations.AlterUniqueTogether(
            name="trackcache",
            unique_together={("artist_key", "track_key")},
        ),
    ]
