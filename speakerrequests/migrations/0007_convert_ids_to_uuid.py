"""Convert speaker request primary keys to UUID, preserving inbound foreign keys."""

import uuid

from django.db import migrations, models

from base.db_migration_utils import FkConstraintSnapshot, enable_pgcrypto

snapshot = FkConstraintSnapshot()

TARGET_PK_TABLES = [
    "speakerrequests_speakerrequest",
]

# Columns converted inside convert_own_columns_to_uuid below.
already_handled = set()

OWN_CONVERSION_STATEMENTS = [
    "ALTER TABLE speakerrequests_speakerrequest ALTER COLUMN id DROP IDENTITY IF EXISTS;",
    "ALTER TABLE speakerrequests_speakerrequest ALTER COLUMN id TYPE uuid USING (gen_random_uuid());",
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
    """Convert speaker request PKs to UUID while preserving inbound foreign keys."""

    dependencies = [
        ("speakerrequests", "0006_alter_speakerrequest_options_and_more"),
        ("profiles", "0012_convert_ids_to_uuid"),
    ]

    operations = [
        migrations.RunPython(enable_pgcrypto, migrations.RunPython.noop),
        migrations.RunPython(drop_inbound_fks, migrations.RunPython.noop),
        migrations.RunPython(convert_own_columns_to_uuid, migrations.RunPython.noop),
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
        migrations.RunPython(restore_inbound_fks, migrations.RunPython.noop),
    ]
