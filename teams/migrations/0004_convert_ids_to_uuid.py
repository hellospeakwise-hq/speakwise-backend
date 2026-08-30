"""Convert teams primary keys to UUID, preserving inbound foreign keys."""

import uuid

from django.db import migrations, models

from base.db_migration_utils import FkConstraintSnapshot, enable_pgcrypto

snapshot = FkConstraintSnapshot()

TARGET_PK_TABLES = [
    "team_member",
    "team_social",
]

# Columns converted inside convert_own_columns_to_uuid below.
already_handled = {
    ("team_social", "team_member_id"),
}

OWN_CONVERSION_STATEMENTS = [
    'ALTER TABLE "team_member" ALTER COLUMN id DROP IDENTITY IF EXISTS;',
    'ALTER TABLE "team_social" ALTER COLUMN id DROP IDENTITY IF EXISTS;',
    'ALTER TABLE "team_member" ALTER COLUMN id TYPE uuid USING (gen_random_uuid());',
    'ALTER TABLE "team_social" ALTER COLUMN id TYPE uuid USING (gen_random_uuid());',
    'ALTER TABLE "team_social" ALTER COLUMN team_member_id DROP NOT NULL;',
    'ALTER TABLE "team_social" ALTER COLUMN team_member_id TYPE uuid USING (NULL);',
]


def drop_inbound_fks(apps, schema_editor):
    """Drop FK constraints referencing the converted tables, capturing definitions."""
    snapshot.drop(schema_editor, TARGET_PK_TABLES, already_handled)


def convert_own_columns_to_uuid(apps, schema_editor):
    """Convert the app's own PK and FK columns to uuid."""
    snapshot.convert_targets(schema_editor, OWN_CONVERSION_STATEMENTS)


def restore_inbound_fks(apps, schema_editor):
    """Re-add every FK constraint dropped for the conversion."""
    snapshot.restore(schema_editor)


class Migration(migrations.Migration):
    """Convert team PKs to UUID while preserving inbound foreign keys."""

    dependencies = [
        ("teams", "0003_alter_teammember_updated_at_alter_teamsocial_link_and_more"),
    ]

    operations = [
        migrations.RunPython(enable_pgcrypto, migrations.RunPython.noop),
        migrations.RunPython(drop_inbound_fks, migrations.RunPython.noop),
        migrations.RunPython(convert_own_columns_to_uuid, migrations.RunPython.noop),
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
        migrations.RunPython(restore_inbound_fks, migrations.RunPython.noop),
    ]
