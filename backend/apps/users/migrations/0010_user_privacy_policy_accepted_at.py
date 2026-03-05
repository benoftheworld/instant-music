"""
Migration : ajout du champ privacy_policy_accepted_at au modèle User.
"""

import django.utils.translation
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0009_user_coins_balance"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="privacy_policy_accepted_at",
            field=models.DateTimeField(
                blank=True,
                help_text=django.utils.translation.gettext_lazy(
                    "Date d'acceptation de la politique de confidentialité."
                ),
                null=True,
                verbose_name="politique de confidentialité acceptée le",
            ),
        ),
    ]
