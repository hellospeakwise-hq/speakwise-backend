import uuid
from django.db import migrations, models


def drop_fk_constraints(apps, schema_editor):
    """Dynamically find and drop ALL FK constraints referencing speakers tables,
    including constraints from other apps (feedbacks, talks, speakerrequests, etc.)."""

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
            cursor.execute(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" TYPE uuid USING (NULL);'
            )


class Migration(migrations.Migration):

    dependencies = [
        ("speakers", "0011_alter_speakerexperiences_updated_at_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS "pgcrypto";',
        ),
        migrations.RunPython(drop_fk_constraints, migrations.RunPython.noop),
        migrations.RunSQL(
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
                "ALTER TABLE speakers_speakerexperiences ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
                "ALTER TABLE speakers_speakerskilltag ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
                "ALTER TABLE speakers_speakersociallinks ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
                "ALTER TABLE speakers_speakerfollow ALTER COLUMN speaker_id TYPE uuid USING (NULL);",
                "ALTER TABLE speakers_speakerprofile_events_spoken ALTER COLUMN speakerprofile_id TYPE uuid USING (NULL);",
            ],
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
        ),
    ]
