"""Merge migrations for organization slug and status fields."""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("organizations", "0002_organization_slug"),
        ("organizations", "0002_organization_status"),
    ]

    operations = []
