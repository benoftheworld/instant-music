from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0020_alter_gameanswer_id_alter_gameplayer_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="gameplayer",
            name="consecutive_correct",
            field=models.IntegerField(
                default=0,
                help_text="Nombre de bonnes réponses consécutives dans la partie",
                verbose_name="série en cours",
            ),
        ),
    ]
