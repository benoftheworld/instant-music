from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("games", "0021_gameplayer_consecutive_correct"),
    ]

    operations = [
        migrations.AddField(
            model_name="gameanswer",
            name="streak_bonus",
            field=models.IntegerField(default=0, verbose_name="bonus série"),
        ),
    ]
