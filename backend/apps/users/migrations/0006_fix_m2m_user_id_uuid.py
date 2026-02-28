# Migration manquante : conversion des tables M2M Django (groups, user_permissions)
# oubliées dans users/0005.
#
# Problème : users_user.id est désormais uuid, mais les tables M2M implicites
# créées par PermissionsMixin ont leur colonne user_id encore en bigint.
# Cela provoque "operator does not exist: integer = uuid" sur le formulaire
# de modification dans l'admin.
#
# Tables concernées :
#   - users_user_groups            (user_id → users_user.id)
#   - users_user_user_permissions  (user_id → users_user.id)
#
# Les contraintes FK avaient déjà été supprimées par le DO block de users/0005.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_alter_friendship_id_alter_team_id_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[
                # users_user_groups
                "ALTER TABLE users_user_groups ALTER COLUMN user_id DROP IDENTITY IF EXISTS",
                "ALTER TABLE users_user_groups ALTER COLUMN user_id DROP DEFAULT",
                "ALTER TABLE users_user_groups ALTER COLUMN user_id TYPE uuid USING gen_random_uuid()",
                # users_user_user_permissions
                "ALTER TABLE users_user_user_permissions ALTER COLUMN user_id DROP IDENTITY IF EXISTS",
                "ALTER TABLE users_user_user_permissions ALTER COLUMN user_id DROP DEFAULT",
                "ALTER TABLE users_user_user_permissions ALTER COLUMN user_id TYPE uuid USING gen_random_uuid()",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
        migrations.RunSQL(
            sql=[
                "ALTER TABLE users_user_groups ADD CONSTRAINT users_user_groups_user_id_fk FOREIGN KEY (user_id) REFERENCES users_user(id) ON DELETE CASCADE",
                "ALTER TABLE users_user_user_permissions ADD CONSTRAINT users_user_user_permissions_user_id_fk FOREIGN KEY (user_id) REFERENCES users_user(id) ON DELETE CASCADE",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
