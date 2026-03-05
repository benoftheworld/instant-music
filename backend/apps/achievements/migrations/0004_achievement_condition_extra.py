# Generated migration — ajoute le champ condition_extra à Achievement.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('achievements', '0003_alter_achievement_id_alter_userachievement_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='achievement',
            name='condition_extra',
            field=models.CharField(
                blank=True,
                max_length=100,
                null=True,
                verbose_name='contexte de condition',
            ),
        ),
    ]
