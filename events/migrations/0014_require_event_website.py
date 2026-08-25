"""Require an event website and clarify submitted_by help text."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def fill_empty_websites(apps, schema_editor):
    """Replace NULL websites so the column can become NOT NULL."""
    Event = apps.get_model("events", "Event")
    Event.objects.filter(website__isnull=True).update(website="")


class Migration(migrations.Migration):
    """Make website required and document why submitted_by can be null."""

    dependencies = [
        ("events", "0013_event_submitted_by"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(fill_empty_websites, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="event",
            name="website",
            field=models.URLField(
                help_text=(
                    "Official event website or a public page about the event "
                    "(for example a LinkedIn post)."
                ),
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="event",
            name="submitted_by",
            field=models.ForeignKey(
                blank=True,
                help_text=(
                    "The user who submitted this event for listing. Null for "
                    "listings created before attribution existed, and if the "
                    "submitter account is later deleted."
                ),
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="submitted_events",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
