"""Add slug field to Organization model.

This migration adds the slug field that was incorrectly baked into
0001_initial.py after the database was already created.
"""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="organization",
            name="slug",
            field=models.SlugField(max_length=255, null=True, unique=True),
        ),
    ]
