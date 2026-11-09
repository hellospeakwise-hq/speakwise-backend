"""Reset any unconfirmed/simulated badges back to eligible so users can claim on-chain."""

from django.db import migrations


def reset_simulated_badges(apps, schema_editor):
    """Reset badges previously marked claimed with simulated hashes."""
    SpeakerBadge = apps.get_model("badges", "SpeakerBadge")
    SpeakerBadge.objects.filter(status="claimed").update(
        status="eligible",
        tx_hash=None,
        claimed_at=None,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("badges", "0002_seed_badge_definitions"),
    ]

    operations = [
        migrations.RunPython(reset_simulated_badges, migrations.RunPython.noop),
    ]

