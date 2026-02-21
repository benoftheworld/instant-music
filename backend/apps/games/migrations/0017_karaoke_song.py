"""
Migration: add KaraokeSong catalogue model and karaoke_song FK on Game.
Also renames the help_text on the legacy karaoke_track JSON field.
"""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0016_track_cache"),
    ]

    operations = [
        # 1. Create the KaraokeSong catalogue table
        migrations.CreateModel(
            name="KaraokeSong",
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
                ("title", models.CharField(max_length=255, verbose_name="titre")),
                ("artist", models.CharField(max_length=255, verbose_name="artiste")),
                (
                    "youtube_video_id",
                    models.CharField(
                        help_text="Identifiant de la vidéo YouTube (ex: dQw4w9WgXcQ)",
                        max_length=20,
                        unique=True,
                        verbose_name="ID vidéo YouTube",
                    ),
                ),
                (
                    "lrclib_id",
                    models.IntegerField(
                        blank=True,
                        help_text=(
                            "ID numérique sur lrclib.net pour récupérer les paroles "
                            "synchronisées directement (évite les recherches par nom)."
                        ),
                        null=True,
                        verbose_name="ID LRCLib",
                    ),
                ),
                (
                    "album_image_url",
                    models.URLField(
                        blank=True,
                        default="",
                        max_length=500,
                        verbose_name="image album",
                    ),
                ),
                (
                    "duration_ms",
                    models.IntegerField(
                        default=0,
                        help_text="Durée en millisecondes",
                        verbose_name="durée (ms)",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Seuls les morceaux actifs sont proposés aux joueurs",
                        verbose_name="actif",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="créé le"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="mis à jour le"),
                ),
            ],
            options={
                "verbose_name": "morceau karaoké",
                "verbose_name_plural": "morceaux karaoké",
                "ordering": ["artist", "title"],
            },
        ),
        # 2. Add karaoke_song FK on Game
        migrations.AddField(
            model_name="game",
            name="karaoke_song",
            field=models.ForeignKey(
                blank=True,
                help_text="Morceau sélectionné depuis le catalogue administré",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="games",
                to="games.karaokesong",
                verbose_name="morceau karaoké",
            ),
        ),
        # 3. Update verbose_name on legacy karaoke_track JSON field
        migrations.AlterField(
            model_name="game",
            name="karaoke_track",
            field=models.JSONField(
                blank=True,
                default=None,
                help_text=(
                    "Champ hérité — préférer karaoke_song. "
                    "Peuplé automatiquement depuis karaoke_song à la création."
                ),
                null=True,
                verbose_name="morceau karaoké (legacy)",
            ),
        ),
    ]
