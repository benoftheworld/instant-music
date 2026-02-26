# Generated migration for new game modes system

from django.db import migrations, models


def migrate_old_modes(apps, schema_editor):
    """Convert old game modes to new ones."""
    Game = apps.get_model("games", "Game")
    mode_mapping = {
        "quiz_4": "classique",
        "blind_test_inverse": "classique",
        "guess_year": "generation",
        "guess_artist": "classique",
        "intro": "rapide",
        "lyrics": "paroles",
    }
    for game in Game.objects.all():
        new_mode = mode_mapping.get(game.mode, "classique")
        Game.objects.filter(pk=game.pk).update(mode=new_mode)


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0012_game_lyrics_words_count"),
    ]

    operations = [
        # Step 1: Add new fields with defaults
        migrations.AddField(
            model_name="game",
            name="guess_target",
            field=models.CharField(
                choices=[("artist", "Artiste"), ("title", "Titre")],
                default="title",
                help_text="En mode QCM Classique/Rapide : deviner l'artiste ou le titre",
                max_length=10,
                verbose_name="cible à deviner",
            ),
        ),
        migrations.AddField(
            model_name="game",
            name="timer_start_round",
            field=models.IntegerField(
                default=5,
                help_text="Compte à rebours avant le début du round (3-15)",
                verbose_name="timer début de round (secondes)",
            ),
        ),
        migrations.AddField(
            model_name="game",
            name="score_display_duration",
            field=models.IntegerField(
                default=10,
                help_text="Durée d'affichage du score en fin de round (3-30)",
                verbose_name="temps affichage score (secondes)",
            ),
        ),
        # Step 2: Remove old fields
        migrations.RemoveField(
            model_name="game",
            name="modes",
        ),
        migrations.RemoveField(
            model_name="game",
            name="time_between_rounds",
        ),
        # Step 3: Migrate old mode values to new ones
        migrations.RunPython(migrate_old_modes, migrations.RunPython.noop),
        # Step 4: Update mode field choices
        migrations.AlterField(
            model_name="game",
            name="mode",
            field=models.CharField(
                choices=[
                    ("classique", "Classique"),
                    ("rapide", "Rapide"),
                    ("generation", "Génération"),
                    ("paroles", "Paroles"),
                ],
                default="classique",
                max_length=20,
                verbose_name="mode de jeu",
            ),
        ),
        # Step 5: Update answer_mode choices
        migrations.AlterField(
            model_name="game",
            name="answer_mode",
            field=models.CharField(
                choices=[("mcq", "QCM"), ("text", "Saisie libre")],
                default="mcq",
                help_text="QCM ou saisie libre",
                max_length=10,
                verbose_name="mode de réponse",
            ),
        ),
        # Step 6: Update lyrics_words_count default and help text
        migrations.AlterField(
            model_name="game",
            name="lyrics_words_count",
            field=models.IntegerField(
                default=3,
                help_text="Nombre de mots à deviner dans le mode Paroles (2-10)",
                verbose_name="nombre de mots à deviner (paroles)",
            ),
        ),
    ]
