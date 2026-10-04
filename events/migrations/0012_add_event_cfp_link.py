# Generated manually for CFP link storage.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0010_alter_country_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="cfp_link",
            field=models.URLField(
                blank=True,
                default="",
                help_text="External URL for the event's CFP page.",
                max_length=255,
            ),
        ),
    ]
