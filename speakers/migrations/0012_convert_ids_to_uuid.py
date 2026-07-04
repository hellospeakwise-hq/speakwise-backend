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
<<<<<<< HEAD
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

=======
>>>>>>> 2dee7cf (model IDs from int to UUID)
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


class Migration(migrations.Migration):
    dependencies = [
        ("speakers", "0011_alter_speakerexperiences_updated_at_and_more"),
    ]

    operations = [
        migrations.RunPython(pgcrypto_if_postgres, migrations.RunPython.noop),
        migrations.RunPython(drop_fk_constraints, migrations.RunPython.noop),
        migrations.RunPython(convert_columns_to_uuid, migrations.RunPython.noop),
<<<<<<< HEAD
        migrations.RunSQL(
<<<<<<< HEAD
            sql=[
                "ALTER TABLE speakers_speakerprofile ALTER COLUMN id DROP IDENTITY IF EXISTS;",
                "ALTER TABLE speakers_speakerexperiences ALTER COLUMN id DROP IDENTITY IF EXISTS;",
                "ALTER TABLE speakers_speakerskilltag ALTER COLUMN id DROP IDENTITY IF EXISTS;",
                "ALTER TABLE speakers_speakersociallinks ALTER COLUMN id DROP IDENTITY IF EXISTS;",
                "ALTER TABLE speakers_speakerfollow ALTER COLUMN id DROP IDENTITY IF EXISTS;",
                "ALTER TABLE speakers_speakerprofile ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
                "ALTER TABLE speakers_speakerexperiences ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
                "ALTER TABLE speakers_speakerskilltag ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
                "ALTER TABLE speakers_speakersociallinks ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
                "ALTER TABLE speakers_speakerfollow ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
<<<<<<< HEAD
                "ALTER TABLE speakers_speakerexperiences ALTER COLUMN speaker_id DROP NOT NULL;",
                "ALTER TABLE speakers_speakerexperiences ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
                "ALTER TABLE speakers_speakerskilltag ALTER COLUMN speaker_id DROP NOT NULL;",
                "ALTER TABLE speakers_speakerskilltag ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
                "ALTER TABLE speakers_speakersociallinks ALTER COLUMN speaker_id DROP NOT NULL;",
                "ALTER TABLE speakers_speakersociallinks ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
                "ALTER TABLE speakers_speakerfollow ALTER COLUMN speaker_id DROP NOT NULL;",
                "ALTER TABLE speakers_speakerfollow ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
                "ALTER TABLE speakers_speakerprofile_events_spoken ALTER COLUMN speakerprofile_id DROP NOT NULL;",
=======
                "ALTER TABLE speakers_speakerexperiences ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
                "ALTER TABLE speakers_speakerskilltag ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
                "ALTER TABLE speakers_speakersociallinks ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
                "ALTER TABLE speakers_speakerfollow ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
>>>>>>> 2dee7cf (model IDs from int to UUID)
                "ALTER TABLE speakers_speakerprofile_events_spoken ALTER COLUMN speakerprofile_id TYPE uuid USING (NULL);",
            ],
=======
            sql=[],
>>>>>>> 903c2e1 (fix migrations failure for test server deployment)
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
            ],
=======
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
        migrations.AlterField(
            model_name="speakerfollow",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
            ),
>>>>>>> 992caa2 (fix test pass between sqlite and postgres)
        ),
    ]
