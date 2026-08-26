"""Add submitted_by and official website help text to Event."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Attach listing submitter and clarify the official website field."""

    dependencies = [
        ("events", "0012_add_event_cfp_link"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="website",
            field=models.URLField(
                blank=True,
                help_text="Official event website URL.",
                max_length=255,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="event",
            name="submitted_by",
            field=models.ForeignKey(
                blank=True,
                help_text="The user who submitted this event for listing.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="submitted_events",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
