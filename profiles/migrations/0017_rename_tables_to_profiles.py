"""Rename speakers_* tables to profiles_* after the app rename."""

from django.db import migrations

TABLE_RENAMES = [
    ("speakers_speakerprofile", "profiles_speakerprofile"),
    ("speakers_speakerexperiences", "profiles_speakerexperiences"),
    ("speakers_speakerskilltag", "profiles_speakerskilltag"),
    ("speakers_speakersociallinks", "profiles_speakersociallinks"),
    ("speakers_speakerfollow", "profiles_speakerfollow"),
    ("speakers_speakerdeck", "profiles_speakerdeck"),
    ("speakers_notification", "profiles_notification"),
    (
        "speakers_speakerprofile_events_spoken",
        "profiles_speakerprofile_events_spoken",
    ),
]


def rename_tables(apps, schema_editor):
    """Rename legacy speakers_* tables; no-op where names already match."""
    if schema_editor.connection.vendor != "postgresql":
        return
    for old_name, new_name in TABLE_RENAMES:
        schema_editor.execute(
            f"ALTER TABLE IF EXISTS {old_name} RENAME TO {new_name};"
        )


def revert_table_names(apps, schema_editor):
    """Restore legacy speakers_* table names."""
    if schema_editor.connection.vendor != "postgresql":
        return
    for old_name, new_name in TABLE_RENAMES:
        schema_editor.execute(
            f"ALTER TABLE IF EXISTS {new_name} RENAME TO {old_name};"
        )


class Migration(migrations.Migration):
    """Rename legacy speaker tables and register the profiles app history."""
    dependencies = [
        ("events", "0013_alter_eventspeakers_options_alter_country_name"),
        ("profiles", "0016_alter_notification_is_read"),
    ]

    operations = [
        migrations.RunPython(rename_tables, revert_table_names),
    ]
