import uuid
from django.db import migrations, models


def pgcrypto_if_postgres(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')


def drop_fk_constraints(apps, schema_editor):
    """Dynamically find and drop ALL FK constraints referencing team tables."""

    if schema_editor.connection.vendor != "postgresql":
        return

    cursor = schema_editor.connection.cursor()
    target_pk_tables = ["team_member", "team_social"]

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
        ("team_social", "team_member_id"),
    }
    for table_name, column_name, constraint_name in fk_constraints:
        if (table_name, column_name) not in already_handled:
            cursor.execute(
<<<<<<< HEAD
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" DROP NOT NULL;'
            )
            cursor.execute(
=======
>>>>>>> 2dee7cf (model IDs from int to UUID)
                f'ALTER TABLE "{table_name}" ALTER COLUMN "{column_name}" TYPE uuid USING (NULL);'
            )


def convert_columns_to_uuid(apps, schema_editor):
    if schema_editor.connection.vendor == "postgresql":
        schema_editor.execute('ALTER TABLE "team_member" ALTER COLUMN id DROP IDENTITY IF EXISTS;')
        schema_editor.execute('ALTER TABLE "team_social" ALTER COLUMN id DROP IDENTITY IF EXISTS;')
        schema_editor.execute('ALTER TABLE "team_member" ALTER COLUMN id TYPE uuid USING (gen_random_uuid());')
        schema_editor.execute('ALTER TABLE "team_social" ALTER COLUMN id TYPE uuid USING (gen_random_uuid());')
        schema_editor.execute('ALTER TABLE "team_social" ALTER COLUMN team_member_id DROP NOT NULL;')
        schema_editor.execute('ALTER TABLE "team_social" ALTER COLUMN team_member_id TYPE uuid USING (NULL);')


class Migration(migrations.Migration):

    dependencies = [
        ("teams", "0003_alter_teammember_updated_at_alter_teamsocial_link_and_more"),
    ]

    operations = [
        migrations.RunPython(pgcrypto_if_postgres, migrations.RunPython.noop),
        migrations.RunPython(drop_fk_constraints, migrations.RunPython.noop),
        migrations.RunPython(convert_columns_to_uuid, migrations.RunPython.noop),
<<<<<<< HEAD
        migrations.RunSQL(
<<<<<<< HEAD
            sql=[
                'ALTER TABLE "team_member" ALTER COLUMN id DROP IDENTITY IF EXISTS;',
                'ALTER TABLE "team_social" ALTER COLUMN id DROP IDENTITY IF EXISTS;',
                'ALTER TABLE "team_member" ALTER COLUMN id TYPE uuid USING (gen_random_uuid());',
                'ALTER TABLE "team_social" ALTER COLUMN id TYPE uuid USING (gen_random_uuid());',
<<<<<<< HEAD
                'ALTER TABLE "team_social" ALTER COLUMN team_member_id DROP NOT NULL;',
=======
>>>>>>> 2dee7cf (model IDs from int to UUID)
                'ALTER TABLE "team_social" ALTER COLUMN team_member_id TYPE uuid USING (NULL);',
            ],
=======
            sql=[],
>>>>>>> 903c2e1 (fix migrations failure for test server deployment)
            state_operations=[
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
                    model_name="teamsocial",
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
            model_name="teamsocial",
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
