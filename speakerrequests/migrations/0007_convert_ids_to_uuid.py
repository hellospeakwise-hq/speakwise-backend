import uuid
from django.db import migrations, models

from base.migration_utils import (
    execute_sql_list_if_postgres,
    is_postgres,
    run_if_postgres,
)


def drop_fk_constraints(apps, schema_editor):
    """Dynamically find and drop ALL FK constraints referencing speakerrequests_speakerrequest table."""

    if not is_postgres(schema_editor):
        return

    cursor = schema_editor.connection.cursor()
    target_pk_tables = ["speakerrequests_speakerrequest"]

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

    already_handled = set()
    for table_name, column_name, constraint_name in fk_constraints:
        if (table_name, column_name) not in already_handled:
            cursor.execute(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" DROP NOT NULL;'
            )
            cursor.execute(
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" TYPE uuid USING (NULL);'
            )


class Migration(migrations.Migration):

    dependencies = [
        ("speakerrequests", "0006_alter_speakerrequest_options_and_more"),
        ("speakers", "0012_convert_ids_to_uuid"),
    ]

    operations = [
        run_if_postgres(
            sql='CREATE EXTENSION IF NOT EXISTS "pgcrypto";',
        ),
        migrations.RunPython(drop_fk_constraints, migrations.RunPython.noop),
        execute_sql_list_if_postgres([
            "ALTER TABLE speakerrequests_speakerrequest ALTER COLUMN id DROP IDENTITY IF EXISTS;",
            "ALTER TABLE speakerrequests_speakerrequest ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
        ]),
        migrations.RunSQL(
            sql=[],
            state_operations=[
                migrations.AlterField(
                    model_name="speakerrequest",
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
