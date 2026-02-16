"""
Add new game modes (blind_test_inverse, guess_year, intro, lyrics)
and new fields on GameRound (question_type, question_text, extra_data).
Remove old unused modes (quiz_fastest, karaoke).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0005_add_preview_url_to_gameround'),
    ]

    operations = [
        # Update Game.mode choices
        migrations.AlterField(
            model_name='game',
            name='mode',
            field=models.CharField(
                choices=[
                    ('quiz_4', 'Quiz 4 réponses'),
                    ('blind_test_inverse', 'Blind Test Inversé'),
                    ('guess_year', 'Année de Sortie'),
                    ('intro', 'Intro (5s)'),
                    ('lyrics', 'Lyrics'),
                ],
                default='quiz_4',
                max_length=20,
                verbose_name='mode de jeu',
            ),
        ),
        # Add question_type to GameRound
        migrations.AddField(
            model_name='gameround',
            name='question_type',
            field=models.CharField(
                default='guess_title',
                max_length=30,
                verbose_name='type de question',
            ),
        ),
        # Add question_text to GameRound
        migrations.AddField(
            model_name='gameround',
            name='question_text',
            field=models.CharField(
                default='Quel est le titre de ce morceau ?',
                max_length=500,
                verbose_name='texte de la question',
            ),
        ),
        # Add extra_data to GameRound
        migrations.AddField(
            model_name='gameround',
            name='extra_data',
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name='données supplémentaires',
            ),
        ),
    ]
