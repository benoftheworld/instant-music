# Réécriture de la migration auto-générée.
# Problème original : AlterField sans clause USING → "cannot cast type bigint to uuid"
# sur PostgreSQL.
#
# Solution : SeparateDatabaseAndState
#   - state_operations  : met à jour le registre Django (AlterField)
#   - database_operations : SQL avec USING gen_random_uuid() + gestion des
#     contraintes FK cross-app (games, achievements) qui référencent users_user
#     et users_team.
#
# Séquence :
#   1. Supprimer les contraintes FK qui référencent les tables modifiées
#   2. Convertir les colonnes PK (DROP DEFAULT + TYPE uuid)
#   3. Supprimer les séquences devenues inutiles
#   4. Convertir les colonnes FK (même app + cross-app)
#   5. Recréer les contraintes FK

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_teamjoinrequest"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # ── État Django ─────────────────────────────────────────────────
            state_operations=[
                migrations.AlterField(
                    model_name="friendship",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="team",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="teamjoinrequest",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="teammember",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="user",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
            ],
            # ── SQL réel ────────────────────────────────────────────────────
            database_operations=[
                # 1. Supprimer toutes les contraintes FK qui référencent
                #    users_user.id ou users_team.id (les PKs qui vont changer).
                migrations.RunSQL(
                    sql="""
DO $$
DECLARE r RECORD;
BEGIN
    FOR r IN
        SELECT c.conname, c.conrelid::regclass::text AS tbl
        FROM pg_constraint c
        WHERE c.contype = 'f'
          AND c.confrelid IN (
              'users_user'::regclass,
              'users_team'::regclass
          )
    LOOP
        EXECUTE format('ALTER TABLE %I DROP CONSTRAINT %I', r.tbl, r.conname);
    END LOOP;
END $$;
""",
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # 2. Convertir les colonnes PK bigint → uuid.
                migrations.RunSQL(
                    sql=[
                        "ALTER TABLE users_user ALTER COLUMN id DROP DEFAULT",
                        "ALTER TABLE users_user ALTER COLUMN id TYPE uuid USING gen_random_uuid()",
                        "DROP SEQUENCE IF EXISTS users_user_id_seq",
                        "ALTER TABLE users_friendship ALTER COLUMN id DROP DEFAULT",
                        "ALTER TABLE users_friendship ALTER COLUMN id TYPE uuid USING gen_random_uuid()",
                        "DROP SEQUENCE IF EXISTS users_friendship_id_seq",
                        "ALTER TABLE users_team ALTER COLUMN id DROP DEFAULT",
                        "ALTER TABLE users_team ALTER COLUMN id TYPE uuid USING gen_random_uuid()",
                        "DROP SEQUENCE IF EXISTS users_team_id_seq",
                        "ALTER TABLE users_teamjoinrequest ALTER COLUMN id DROP DEFAULT",
                        "ALTER TABLE users_teamjoinrequest ALTER COLUMN id TYPE uuid USING gen_random_uuid()",
                        "DROP SEQUENCE IF EXISTS users_teamjoinrequest_id_seq",
                        "ALTER TABLE users_teammember ALTER COLUMN id DROP DEFAULT",
                        "ALTER TABLE users_teammember ALTER COLUMN id TYPE uuid USING gen_random_uuid()",
                        "DROP SEQUENCE IF EXISTS users_teammember_id_seq",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # 3. Convertir les colonnes FK (même app + cross-app).
                migrations.RunSQL(
                    sql=[
                        # users_friendship
                        "ALTER TABLE users_friendship ALTER COLUMN from_user_id TYPE uuid USING gen_random_uuid()",
                        "ALTER TABLE users_friendship ALTER COLUMN to_user_id TYPE uuid USING gen_random_uuid()",
                        # users_team
                        "ALTER TABLE users_team ALTER COLUMN owner_id TYPE uuid USING gen_random_uuid()",
                        # users_teammember
                        "ALTER TABLE users_teammember ALTER COLUMN user_id TYPE uuid USING gen_random_uuid()",
                        "ALTER TABLE users_teammember ALTER COLUMN team_id TYPE uuid USING gen_random_uuid()",
                        # users_teamjoinrequest
                        "ALTER TABLE users_teamjoinrequest ALTER COLUMN user_id TYPE uuid USING gen_random_uuid()",
                        "ALTER TABLE users_teamjoinrequest ALTER COLUMN team_id TYPE uuid USING gen_random_uuid()",
                        # Cross-app : games_gameplayer.user_id et games_game.host_id
                        "ALTER TABLE games_gameplayer ALTER COLUMN user_id TYPE uuid USING gen_random_uuid()",
                        "ALTER TABLE games_game ALTER COLUMN host_id TYPE uuid USING gen_random_uuid()",
                        # Cross-app : achievements_userachievement.user_id
                        "ALTER TABLE achievements_userachievement ALTER COLUMN user_id TYPE uuid USING gen_random_uuid()",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # 4. Recréer les contraintes FK avec les nouveaux types UUID.
                migrations.RunSQL(
                    sql=[
                        # users_friendship
                        "ALTER TABLE users_friendship ADD CONSTRAINT users_friendship_from_user_id_fk FOREIGN KEY (from_user_id) REFERENCES users_user(id) ON DELETE CASCADE",
                        "ALTER TABLE users_friendship ADD CONSTRAINT users_friendship_to_user_id_fk FOREIGN KEY (to_user_id) REFERENCES users_user(id) ON DELETE CASCADE",
                        # users_team
                        "ALTER TABLE users_team ADD CONSTRAINT users_team_owner_id_fk FOREIGN KEY (owner_id) REFERENCES users_user(id) ON DELETE CASCADE",
                        # users_teammember
                        "ALTER TABLE users_teammember ADD CONSTRAINT users_teammember_team_id_fk FOREIGN KEY (team_id) REFERENCES users_team(id) ON DELETE CASCADE",
                        "ALTER TABLE users_teammember ADD CONSTRAINT users_teammember_user_id_fk FOREIGN KEY (user_id) REFERENCES users_user(id) ON DELETE CASCADE",
                        # users_teamjoinrequest
                        "ALTER TABLE users_teamjoinrequest ADD CONSTRAINT users_teamjoinrequest_team_id_fk FOREIGN KEY (team_id) REFERENCES users_team(id) ON DELETE CASCADE",
                        "ALTER TABLE users_teamjoinrequest ADD CONSTRAINT users_teamjoinrequest_user_id_fk FOREIGN KEY (user_id) REFERENCES users_user(id) ON DELETE CASCADE",
                        # Cross-app : games
                        "ALTER TABLE games_gameplayer ADD CONSTRAINT games_gameplayer_user_id_fk FOREIGN KEY (user_id) REFERENCES users_user(id) ON DELETE CASCADE",
                        "ALTER TABLE games_game ADD CONSTRAINT games_game_host_id_fk FOREIGN KEY (host_id) REFERENCES users_user(id) ON DELETE CASCADE",
                        # Cross-app : achievements
                        "ALTER TABLE achievements_userachievement ADD CONSTRAINT achievements_userachievement_user_id_fk FOREIGN KEY (user_id) REFERENCES users_user(id) ON DELETE CASCADE",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
