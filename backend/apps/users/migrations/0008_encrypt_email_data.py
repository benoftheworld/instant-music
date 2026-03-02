"""Migration de données : chiffrement des emails existants (RGPD).

Pour chaque utilisateur, chiffre l'email en clair avec Fernet et calcule
le HMAC-SHA256 (email_hash) utilisé pour les lookups ORM.
Ajoute ensuite la contrainte UNIQUE sur email_hash.

Prérequis : les variables EMAIL_ENCRYPTION_KEY et EMAIL_HASH_KEY doivent
être définies dans les settings avant d'appliquer cette migration.
"""

from django.db import migrations

from apps.users.encryption import encrypt_email, hash_email


def encrypt_existing_emails(apps, schema_editor):
    """Chiffre les emails en clair et calcule leur hash pour tous les utilisateurs."""
    User = apps.get_model("users", "User")

    for user in User.objects.all():
        raw_email = user.email
        if not raw_email:
            continue

        # Si l'email est déjà un token Fernet, il a déjà été chiffré
        if raw_email.startswith("gAAAAA"):
            # Recalculer uniquement le hash s'il est manquant
            if not user.email_hash:
                from apps.users.encryption import decrypt_email

                user.email_hash = hash_email(decrypt_email(raw_email))
                user.save(update_fields=["email_hash"])
            continue

        user.email = encrypt_email(raw_email)
        user.email_hash = hash_email(raw_email)
        user.save(update_fields=["email", "email_hash"])


def noop_reverse(apps, schema_editor):
    """Impossible de déchiffrer les emails de manière sûre lors d'un rollback."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0007_encrypt_email"),
    ]

    operations = [
        migrations.RunPython(encrypt_existing_emails, noop_reverse),
        # Ajouter la contrainte UNIQUE sur email_hash après avoir rempli la colonne
        migrations.RunSQL(
            sql="ALTER TABLE users_user ADD CONSTRAINT users_user_email_hash_uniq UNIQUE (email_hash);",
            reverse_sql="ALTER TABLE users_user DROP CONSTRAINT IF EXISTS users_user_email_hash_uniq;",
        ),
    ]
