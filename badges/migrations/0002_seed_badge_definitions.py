"""Seed initial Web3 Soulbound Badge definitions."""

from django.db import migrations

BADGE_DATA = [
    {
        "token_id": 1,
        "name": "Genesis Speaker",
        "slug": "genesis-speaker",
        "tier": "bronze",
        "icon": "Mic",
        "emoji": "🎤",
        "description": "Delivered their very first verified talk experience on SpeakWise.",
        "criteria": "Add 1 verified speaking experience to your profile",
        "metric_type": "talks_count",
        "metric_threshold": 1.0,
    },
    {
        "token_id": 2,
        "name": "In Demand",
        "slug": "in-demand",
        "tier": "silver",
        "icon": "Award",
        "emoji": "⭐",
        "description": "Received and officially accepted their first direct event invitation.",
        "criteria": "Accept 1 direct speaking invitation from an organizer",
        "metric_type": "requests_count",
        "metric_threshold": 1.0,
    },
    {
        "token_id": 3,
        "name": "Crowd Catalyst",
        "slug": "crowd-catalyst",
        "tier": "bronze",
        "icon": "Users",
        "emoji": "🔥",
        "description": "Gathered active audience engagement with 5+ community feedbacks.",
        "criteria": "Collect 5 or more audience feedbacks across talks",
        "metric_type": "feedbacks_count",
        "metric_threshold": 5.0,
    },
    {
        "token_id": 4,
        "name": "Road Warrior",
        "slug": "road-warrior",
        "tier": "silver",
        "icon": "Globe",
        "emoji": "🌍",
        "description": "Demonstrated sustained impact with 3 or more speaking presentations.",
        "criteria": "Present talks at 3 or more distinct events",
        "metric_type": "talks_count",
        "metric_threshold": 3.0,
    },
    {
        "token_id": 5,
        "name": "Five-Star Orator",
        "slug": "five-star-orator",
        "tier": "gold",
        "icon": "Sparkles",
        "emoji": "✨",
        "description": "Maintained an exceptional average rating of 4.8+ across at least 3 rated talks.",
        "criteria": "Achieve 4.8+ average audience rating (min 3 feedbacks)",
        "metric_type": "rating_avg",
        "metric_threshold": 4.8,
    },
    {
        "token_id": 6,
        "name": "Keynote Pioneer",
        "slug": "keynote-pioneer",
        "tier": "gold",
        "icon": "Trophy",
        "emoji": "🏆",
        "description": "Reached a legendary milestone of 10 verified speaking appearances.",
        "criteria": "Deliver 10 verified speaking presentations on SpeakWise",
        "metric_type": "talks_count",
        "metric_threshold": 10.0,
    },
]


def seed_badges(apps, schema_editor):
    BadgeDefinition = apps.get_model("badges", "BadgeDefinition")
    for item in BADGE_DATA:
        BadgeDefinition.objects.update_or_create(
            token_id=item["token_id"],
            defaults=item,
        )


def unseed_badges(apps, schema_editor):
    BadgeDefinition = apps.get_model("badges", "BadgeDefinition")
    token_ids = [item["token_id"] for item in BADGE_DATA]
    BadgeDefinition.objects.filter(token_id__in=token_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("badges", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_badges, unseed_badges),
    ]

