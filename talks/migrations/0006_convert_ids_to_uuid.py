"""Convert talks primary keys to UUID, preserving inbound foreign keys."""

import uuid

from django.db import migrations, models

from base.db_migration_utils import FkConstraintSnapshot, enable_pgcrypto

snapshot = FkConstraintSnapshot()

TARGET_PK_TABLES = [
    "talks_talks",
    "talks_session",
]

# Columns converted inside convert_own_columns_to_uuid below.
already_handled = {
    ("talks_session", "talk_id"),
    ("talks_talkreviewcomment", "talk_id"),
}

OWN_CONVERSION_STATEMENTS = [
    "ALTER TABLE talks_talks ALTER COLUMN id DROP IDENTITY IF EXISTS;",
    "ALTER TABLE talks_session ALTER COLUMN id DROP IDENTITY IF EXISTS;",
    "ALTER TABLE talks_talks ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
    "ALTER TABLE talks_session ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
    "ALTER TABLE talks_session ALTER COLUMN talk_id DROP NOT NULL;",
    "ALTER TABLE talks_session ALTER COLUMN talk_id TYPE uuid USING (NULL);",
    "ALTER TABLE talks_talkreviewcomment ALTER COLUMN talk_id DROP NOT NULL;",
    "ALTER TABLE talks_talkreviewcomment ALTER COLUMN talk_id TYPE uuid USING (NULL);",
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
    """Convert talk and session PKs to UUID while preserving inbound foreign keys."""

    dependencies = [
        ("talks", "0005_make_event_optional_for_standalone_talks"),
        ("profiles", "0012_convert_ids_to_uuid"),
    ]

    operations = [
        migrations.RunPython(enable_pgcrypto, migrations.RunPython.noop),
        migrations.RunPython(drop_inbound_fks, migrations.RunPython.noop),
        migrations.RunPython(convert_own_columns_to_uuid, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="talks",
            name="id",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                primary_key=True,
                serialize=False,
            ),
        ),
        migrations.AlterField(
            model_name="session",
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
