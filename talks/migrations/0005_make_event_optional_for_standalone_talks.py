"""Make event FK optional for standalone pre-CFP talks."""

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Migration to allow talks to exist without an event."""

    dependencies = [
        ("events", "0001_initial"),
        ("talks", "0004_talkreviewcomment_rating_talks_is_public_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="talks",
            name="event",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="talk_event",
                to="events.event",
            ),
        ),
    ]
