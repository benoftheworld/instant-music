# Réécriture de la migration auto-générée.
# Problème original : AlterField sans clause USING → "cannot cast type bigint to uuid".
#
# Dépendance sur users/0005 ajoutée car achievements_userachievement.user_id
# a déjà été converti en uuid par users/0005 (cross-app).
# Cette migration gère uniquement :
#   - PKs : achievement.id, userachievement.id
#   - FK  : userachievement.achievement_id → achievement.id

from django.db import migrations, models
import uuid


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
                # 3. Convertir la colonne FK userachievement.achievement_id.
                #    userachievement.user_id est déjà uuid (converti par users/0005).
                migrations.RunSQL(
                    sql=[
                        "ALTER TABLE achievements_userachievement ALTER COLUMN achievement_id TYPE uuid USING gen_random_uuid()",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # 4. Recréer la contrainte FK.
                migrations.RunSQL(
                    sql=[
                        "ALTER TABLE achievements_userachievement ADD CONSTRAINT achievements_userachievement_achievement_id_fk FOREIGN KEY (achievement_id) REFERENCES achievements_achievement(id) ON DELETE CASCADE",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
