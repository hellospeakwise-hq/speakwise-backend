import uuid

from django.db import migrations, models


def pgcrypto_if_postgres(apps, schema_editor):
    """Enable pgcrypto extension on PostgreSQL (needed for gen_random_uuid)."""
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')


def drop_fk_constraints(apps, schema_editor):
    """Dynamically find and drop ALL FK constraints referencing speakers tables,
    including constraints from other apps (feedbacks, talks, speakerrequests, etc.).
    """
    if schema_editor.connection.vendor != "postgresql":
        return

    cursor = schema_editor.connection.cursor()
    target_pk_tables = [
        "speakers_speakerprofile",
        "speakers_speakerexperiences",
        "speakers_speakerskilltag",
        "speakers_speakersociallinks",
        "speakers_speakerfollow",
    ]

    cursor.execute(
        """
        SELECT
            tc.table_name,
            kcu.column_name,
            tc.constraint_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
          ON tc.constraint_name = kcu.constraint_name
          AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON tc.constraint_name = ccu.constraint_name
          AND tc.table_schema = ccu.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
          AND ccu.table_name = ANY(%s);
        """,
        [target_pk_tables],
    )
    fk_constraints = cursor.fetchall()

    for table_name, column_name, constraint_name in fk_constraints:
        cursor.execute(
            f'ALTER TABLE "{table_name}" DROP CONSTRAINT "{constraint_name}";'
        )

    # These FK columns are handled in the RunSQL block below
    already_handled = {
        ("speakers_speakerexperiences", "speaker_id"),
        ("speakers_speakerskilltag", "speaker_id"),
        ("speakers_speakersociallinks", "speaker_id"),
        ("speakers_speakerfollow", "speaker_id"),
        ("speakers_speakerprofile_events_spoken", "speakerprofile_id"),
    }
    for table_name, column_name, constraint_name in fk_constraints:
        if (table_name, column_name) not in already_handled:
            # Check if column is NOT NULL
            cursor.execute(
                f"""
                SELECT is_nullable
                FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s;
                """,
                [table_name, column_name],
            )
            is_nullable = cursor.fetchone()[0] == "YES"

            if not is_nullable:
                cursor.execute(
                    f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" DROP NOT NULL;'
                )

            cursor.execute(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" TYPE uuid USING (NULL);'
            )


def convert_columns_to_uuid(apps, schema_editor):
    """Convert columns to UUID."""
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute(
            "ALTER TABLE speakers_speakerprofile ALTER COLUMN id DROP IDENTITY IF EXISTS;"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerexperiences ALTER COLUMN id DROP IDENTITY IF EXISTS;"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerskilltag ALTER COLUMN id DROP IDENTITY IF EXISTS;"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakersociallinks ALTER COLUMN id DROP IDENTITY IF EXISTS;"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerfollow ALTER COLUMN id DROP IDENTITY IF EXISTS;"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerprofile ALTER COLUMN id TYPE uuid USING (gen_random_uuid());"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerexperiences ALTER COLUMN id TYPE uuid USING (gen_random_uuid());"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerskilltag ALTER COLUMN id TYPE uuid USING (gen_random_uuid());"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakersociallinks ALTER COLUMN id TYPE uuid USING (gen_random_uuid());"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerfollow ALTER COLUMN id TYPE uuid USING (gen_random_uuid());"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerexperiences ALTER COLUMN speaker_id DROP NOT NULL;"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerexperiences ALTER COLUMN speaker_id TYPE uuid USING (NULL);"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerskilltag ALTER COLUMN speaker_id DROP NOT NULL;"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerskilltag ALTER COLUMN speaker_id TYPE uuid USING (NULL);"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakersociallinks ALTER COLUMN speaker_id DROP NOT NULL;"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakersociallinks ALTER COLUMN speaker_id TYPE uuid USING (NULL);"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerfollow ALTER COLUMN speaker_id DROP NOT NULL;"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerfollow ALTER COLUMN speaker_id TYPE uuid USING (NULL);"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerprofile_events_spoken ALTER COLUMN speakerprofile_id DROP NOT NULL;"
        )
        schema_editor.execute(
            "ALTER TABLE speakers_speakerprofile_events_spoken ALTER COLUMN speakerprofile_id TYPE uuid USING (NULL);"
        )


def restore_fk_constraints(apps, schema_editor):
    """Recreate the FK constraints dropped by drop_fk_constraints.

    Referenced rows were regenerated with random UUIDs, so existing values in
    the referencing columns cannot be preserved (they are nulled out during the
    conversion). Columns whose model fields disallow NULL are restored to
    NOT NULL — safe here because the conversion nulls every value anyway and
    these tables are expected to be repopulated after the migration.
    """
    if schema_editor.connection.vendor != "postgresql":
        return

    cursor = schema_editor.connection.cursor()

    def add_fk_if_not_exists(table, column, ref_table, ref_column, constraint_name):
        """Add an FK constraint only when an equivalent one is not present."""
        cursor.execute(
            """
            SELECT 1 FROM information_schema.table_constraints
            WHERE table_name = %s AND constraint_name = %s;
            """,
            [table, constraint_name],
        )
        if cursor.fetchone():
            return
        cursor.execute(
            f'ALTER TABLE "{table}" ADD CONSTRAINT "{constraint_name}" '
            f'FOREIGN KEY ("{column}") REFERENCES "{ref_table}" ("{ref_column}") '
            f"DEFERRABLE INITIALLY DEFERRED;"
        )

    def set_not_null_if_needed(table, column):
        """Restore NOT NULL only when the column holds no NULL values."""
        cursor.execute(
            f'SELECT COUNT(*) FROM "{table}" WHERE "{column}" IS NULL;'
        )
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                f'ALTER TABLE "{table}" ALTER COLUMN "{column}" SET NOT NULL;'
            )

    set_not_null_if_needed("speakers_speakersociallinks", "speaker_id")
    set_not_null_if_needed("speakers_speakerfollow", "speaker_id")
    set_not_null_if_needed(
        "speakers_speakerprofile_events_spoken", "speakerprofile_id"
    )
    set_not_null_if_needed("events_eventspeakers", "speaker_id")

    add_fk_if_not_exists(
        "speakers_speakerexperiences",
        "speaker_id",
        "speakers_speakerprofile",
        "id",
        "fk_speakerexperiences_speaker_uuid",
    )
    add_fk_if_not_exists(
        "speakers_speakerskilltag",
        "speaker_id",
        "speakers_speakerprofile",
        "id",
        "fk_speakerskilltag_speaker_uuid",
    )
    add_fk_if_not_exists(
        "speakers_speakersociallinks",
        "speaker_id",
        "speakers_speakerprofile",
        "id",
        "fk_speakersociallinks_speaker_uuid",
    )
    add_fk_if_not_exists(
        "speakers_speakerfollow",
        "speaker_id",
        "speakers_speakerprofile",
        "id",
        "fk_speakerfollow_speaker_uuid",
    )
    add_fk_if_not_exists(
        "speakers_speakerprofile_events_spoken",
        "speakerprofile_id",
        "speakers_speakerprofile",
        "id",
        "fk_speakerprofile_events_spoken_speakerprofile_uuid",
    )
    add_fk_if_not_exists(
        "events_eventspeakers",
        "speaker_id",
        "speakers_speakerprofile",
        "id",
        "fk_eventspeakers_speaker_uuid",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("speakers", "0011_alter_speakerexperiences_updated_at_and_more"),
    ]

    operations = [
        migrations.RunPython(pgcrypto_if_postgres, migrations.RunPython.noop),
        migrations.RunPython(drop_fk_constraints, migrations.RunPython.noop),
        migrations.RunPython(convert_columns_to_uuid, migrations.RunPython.noop),
        # State-only syncs: the database columns were converted by the raw SQL
        # above. Running these as regular AlterField operations would make the
        # schema editor try to reconcile every related table itself (including
        # cross-app FKs and long-removed m2m through tables), producing invalid
        # DDL such as casting uuid columns back to bigint.
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="speakerprofile",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
            ]
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="speakerexperiences",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
            ]
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="speakerskilltag",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
            ]
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="speakersociallinks",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
            ]
        ),
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AlterField(
                    model_name="speakerfollow",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
            ]
        ),
        migrations.RunPython(restore_fk_constraints, migrations.RunPython.noop),
    ]
