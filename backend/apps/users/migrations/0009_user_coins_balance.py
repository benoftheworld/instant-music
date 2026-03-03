"""
Migration : ajout du champ coins_balance au modèle User.
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0008_encrypt_email_data"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="coins_balance",
            field=models.IntegerField(
                default=0,
                help_text="Pièces accumulées via les achievements, utilisables dans la boutique",
                verbose_name="solde de pièces",
            ),
        ),
    ]
