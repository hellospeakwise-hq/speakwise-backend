import uuid
from django.db import migrations, models


def drop_fk_constraints(apps, schema_editor):
    """Dynamically find and drop ALL FK constraints referencing attendees tables."""

    cursor = schema_editor.connection.cursor()
    target_pk_tables = [
        "attendees_attendeeprofile",
        "attendees_attendeesociallinks",
        "attendees_attendance",
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
        ("attendees_attendeesociallinks", "attendee_id"),
    }
    for table_name, column_name, constraint_name in fk_constraints:
        if (table_name, column_name) not in already_handled:
            cursor.execute(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" TYPE uuid USING (NULL);'
            )


class Migration(migrations.Migration):

    dependencies = [
        ("attendees", "0006_alter_attendance_updated_at_and_more"),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS "pgcrypto";',
        ),
        migrations.RunPython(drop_fk_constraints, migrations.RunPython.noop),
        migrations.RunSQL(
            sql=[
                "ALTER TABLE attendees_attendeeprofile ALTER COLUMN id DROP IDENTITY IF EXISTS;",
                "ALTER TABLE attendees_attendeesociallinks ALTER COLUMN id DROP IDENTITY IF EXISTS;",
                "ALTER TABLE attendees_attendance ALTER COLUMN id DROP IDENTITY IF EXISTS;",
                "ALTER TABLE attendees_attendeeprofile ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
                "ALTER TABLE attendees_attendeesociallinks ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
                "ALTER TABLE attendees_attendance ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
                "ALTER TABLE attendees_attendeesociallinks ALTER COLUMN attendee_id TYPE uuid USING (NULL);",
            ],
            state_operations=[
                migrations.AlterField(
                    model_name="attendeeprofile",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="attendeesociallinks",
                    name="id",
                    field=models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                migrations.AlterField(
                    model_name="attendance",
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
