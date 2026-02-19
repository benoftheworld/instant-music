# Generated manually for lyrics_words_count field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('games', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='lyrics_words_count',
            field=models.IntegerField(default=1, help_text='Nombre de mots à blanker dans le mode Lyrics (1-3)', verbose_name='nombre de mots à deviner (lyrics)'),
        ),
    ]
