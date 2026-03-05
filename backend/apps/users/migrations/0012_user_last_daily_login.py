# Generated migration — ajoute le champ last_daily_login à User.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0011_alter_user_email_alter_user_email_hash"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="last_daily_login",
            field=models.DateField(
                blank=True,
                help_text="Date de la dernière connexion ayant donné le bonus quotidien.",
                null=True,
                verbose_name="dernière connexion quotidienne",
            ),
        ),
    ]
