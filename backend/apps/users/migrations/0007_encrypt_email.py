"""Migration structurelle : chiffrement de l'email (RGPD).

Ajoute le champ email_hash (HMAC-SHA256) et change email de EmailField
en TextField pour stocker la valeur chiffrée (Fernet AES-128).
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0006_fix_m2m_user_id_uuid"),
    ]

    operations = [
        # 1. Supprimer la contrainte UNIQUE sur email (sera portée par email_hash)
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.TextField(verbose_name="email address"),
        ),
        # 2. Ajouter email_hash (nullable d'abord, la migration de données le remplira)
        migrations.AddField(
            model_name="user",
            name="email_hash",
            field=models.CharField(
                db_index=True,
                default="",
                editable=False,
                max_length=64,
                verbose_name="email hash",
            ),
            preserve_default=False,
        ),
    ]
