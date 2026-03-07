# Migration: mise à jour du champ User.avatar — ajout du validateur validate_avatar
# et mise à jour du help_text.

import apps.users.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0012_user_last_daily_login"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="avatar",
            field=models.ImageField(
                blank=True,
                help_text="Photo de profil (max 5 Mo, JPEG/PNG/WebP/GIF)",
                null=True,
                upload_to="avatars/",
                validators=[apps.users.validators.validate_avatar],
                verbose_name="avatar",
            ),
        ),
    ]
