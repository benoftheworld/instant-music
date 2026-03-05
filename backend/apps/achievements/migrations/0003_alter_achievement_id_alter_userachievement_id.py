# Réécriture de la migration auto-générée.
# Problème original : AlterField sans clause USING → "cannot cast type bigint to uuid".
#
# Dépendance sur users/0005 pour garantir que users_user.id est uuid.
# Cette migration gère :
#   - PKs : achievement.id, userachievement.id
#   - FK interne : userachievement.achievement_id → achievement.id
#   - FK cross-app : userachievement.user_id → users_user.id
#     (contrainte supprimée par users/0005, colonne convertie ici)

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("achievements", "0002_initial"),
        # users/0005 a déjà converti userachievement.user_id en uuid (cross-app).
        ("users", "0005_alter_friendship_id_alter_team_id_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # ── État Django ─────────────────────────────────────────────────
            state_operations=[
                migrations.AlterField(
                    model_name="achievement",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="userachievement",
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
                # 1. Supprimer la contrainte FK userachievement.achievement_id
                #    qui référence achievements_achievement.id (PK en cours de conversion).
                migrations.RunSQL(
                    sql="""
DO $$
DECLARE r RECORD;
BEGIN
    FOR r IN
        SELECT c.conname, c.conrelid::regclass::text AS tbl
        FROM pg_constraint c
        WHERE c.contype = 'f'
          AND c.confrelid = 'achievements_achievement'::regclass
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
                        "ALTER TABLE achievements_achievement ALTER COLUMN id DROP IDENTITY IF EXISTS",
                        "ALTER TABLE achievements_achievement ALTER COLUMN id DROP DEFAULT",
                        "ALTER TABLE achievements_achievement ALTER COLUMN id TYPE uuid USING gen_random_uuid()",
                        "DROP SEQUENCE IF EXISTS achievements_achievement_id_seq",
                        "ALTER TABLE achievements_userachievement ALTER COLUMN id DROP IDENTITY IF EXISTS",
                        "ALTER TABLE achievements_userachievement ALTER COLUMN id DROP DEFAULT",
                        "ALTER TABLE achievements_userachievement ALTER COLUMN id TYPE uuid USING gen_random_uuid()",
                        "DROP SEQUENCE IF EXISTS achievements_userachievement_id_seq",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # 3. Convertir les colonnes FK.
                #    userachievement.user_id : contrainte supprimée par users/0005,
                #    colonne encore en bigint → convertir ici.
                migrations.RunSQL(
                    sql=[
                        "ALTER TABLE achievements_userachievement ALTER COLUMN achievement_id TYPE uuid USING gen_random_uuid()",
                        # Cross-app : userachievement.user_id → users_user.id
                        "ALTER TABLE achievements_userachievement ALTER COLUMN user_id TYPE uuid USING gen_random_uuid()",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # 4. Recréer les contraintes FK.
                migrations.RunSQL(
                    sql=[
                        "ALTER TABLE achievements_userachievement ADD CONSTRAINT achievements_userachievement_achievement_id_fk FOREIGN KEY (achievement_id) REFERENCES achievements_achievement(id) ON DELETE CASCADE",
                        # Cross-app : userachievement.user_id → users_user (CASCADE)
                        "ALTER TABLE achievements_userachievement ADD CONSTRAINT achievements_userachievement_user_id_fk FOREIGN KEY (user_id) REFERENCES users_user(id) ON DELETE CASCADE",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
