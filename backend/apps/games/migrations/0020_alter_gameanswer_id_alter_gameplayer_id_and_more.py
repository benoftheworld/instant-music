# Réécriture de la migration auto-générée.
# Problème original : AlterField sans clause USING → "cannot cast type bigint to uuid".
#
# Solution : SeparateDatabaseAndState avec RunSQL explicite.
#
# Dépendance sur users/0005 ajoutée pour garantir que :
#   - users_user.id est déjà uuid quand cette migration tourne
#   - games_gameplayer.user_id et games_game.host_id sont déjà uuid
#     (convertis par la migration users/0005 en cross-app)
#
# Cette migration gère uniquement :
#   - PKs : gameanswer.id, gameplayer.id, gameround.id, karaokesong.id
#   - FKs dans games qui référencent ces PKs :
#       gameanswer.round_id, gameanswer.player_id, game.karaoke_song_id

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("games", "0019_add_is_public_and_playlist_info"),
        # Nécessaire : users/0005 convertit users_user.id en uuid et met à jour
        # games_gameplayer.user_id / games_game.host_id (cross-app).
        ("users", "0005_alter_friendship_id_alter_team_id_and_more"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            # ── État Django ─────────────────────────────────────────────────
            state_operations=[
                migrations.AlterField(
                    model_name="gameanswer",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="gameplayer",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="gameround",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="karaokesong",
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
                # 1. Supprimer les contraintes FK qui référencent les PKs
                #    en cours de conversion (gameplayer, gameround, karaokesong).
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
              'games_gameplayer'::regclass,
              'games_gameround'::regclass,
              'games_karaokesong'::regclass
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
                        "ALTER TABLE games_gameanswer ALTER COLUMN id DROP DEFAULT",
                        "ALTER TABLE games_gameanswer ALTER COLUMN id TYPE uuid USING gen_random_uuid()",
                        "DROP SEQUENCE IF EXISTS games_gameanswer_id_seq",
                        "ALTER TABLE games_gameplayer ALTER COLUMN id DROP DEFAULT",
                        "ALTER TABLE games_gameplayer ALTER COLUMN id TYPE uuid USING gen_random_uuid()",
                        "DROP SEQUENCE IF EXISTS games_gameplayer_id_seq",
                        "ALTER TABLE games_gameround ALTER COLUMN id DROP DEFAULT",
                        "ALTER TABLE games_gameround ALTER COLUMN id TYPE uuid USING gen_random_uuid()",
                        "DROP SEQUENCE IF EXISTS games_gameround_id_seq",
                        "ALTER TABLE games_karaokesong ALTER COLUMN id DROP DEFAULT",
                        "ALTER TABLE games_karaokesong ALTER COLUMN id TYPE uuid USING gen_random_uuid()",
                        "DROP SEQUENCE IF EXISTS games_karaokesong_id_seq",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # 3. Convertir les colonnes FK dans les tables games qui
                #    référençaient les PKs modifiées ci-dessus.
                #    Remarque : gameplayer.user_id et game.host_id sont déjà
                #    en uuid (traités par users/0005).
                migrations.RunSQL(
                    sql=[
                        # gameanswer.round_id → gameround.id
                        "ALTER TABLE games_gameanswer ALTER COLUMN round_id TYPE uuid USING gen_random_uuid()",
                        # gameanswer.player_id → gameplayer.id
                        "ALTER TABLE games_gameanswer ALTER COLUMN player_id TYPE uuid USING gen_random_uuid()",
                        # game.karaoke_song_id → karaokesong.id (nullable)
                        "ALTER TABLE games_game ALTER COLUMN karaoke_song_id TYPE uuid USING NULL::uuid",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
                # 4. Recréer les contraintes FK avec les nouveaux types UUID.
                migrations.RunSQL(
                    sql=[
                        # gameanswer.round_id → gameround (CASCADE)
                        "ALTER TABLE games_gameanswer ADD CONSTRAINT games_gameanswer_round_id_fk FOREIGN KEY (round_id) REFERENCES games_gameround(id) ON DELETE CASCADE",
                        # gameanswer.player_id → gameplayer (CASCADE)
                        "ALTER TABLE games_gameanswer ADD CONSTRAINT games_gameanswer_player_id_fk FOREIGN KEY (player_id) REFERENCES games_gameplayer(id) ON DELETE CASCADE",
                        # game.karaoke_song_id → karaokesong (SET NULL, nullable)
                        "ALTER TABLE games_game ADD CONSTRAINT games_game_karaoke_song_id_fk FOREIGN KEY (karaoke_song_id) REFERENCES games_karaokesong(id) ON DELETE SET NULL",
                    ],
                    reverse_sql=migrations.RunSQL.noop,
                ),
            ],
        ),
    ]
