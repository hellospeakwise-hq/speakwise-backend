"""Management command to seed initial Web3 Badge definitions."""

from django.core.management.base import BaseCommand
from badges.models import BadgeDefinition, BadgeTierChoices


BADGE_DATA = [
    {
        "token_id": 1,
        "name": "Genesis Speaker",
        "slug": "genesis-speaker",
        "tier": BadgeTierChoices.BRONZE,
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
        "tier": BadgeTierChoices.SILVER,
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
        "tier": BadgeTierChoices.BRONZE,
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
        "tier": BadgeTierChoices.SILVER,
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
        "tier": BadgeTierChoices.GOLD,
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
        "tier": BadgeTierChoices.GOLD,
        "icon": "Trophy",
        "emoji": "🏆",
        "description": "Reached a legendary milestone of 10 verified speaking appearances.",
        "criteria": "Deliver 10 verified speaking presentations on SpeakWise",
        "metric_type": "talks_count",
        "metric_threshold": 10.0,
    },
]


class Command(BaseCommand):
    help = "Seeds initial Web3 Soulbound badge definitions."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for item in BADGE_DATA:
            token_id = item["token_id"]
            badge, created = BadgeDefinition.objects.update_or_create(
                token_id=token_id,
                defaults=item,
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created badge #{token_id}: {badge.name}"))
            else:
                updated_count += 1
                self.stdout.write(f"Updated badge #{token_id}: {badge.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed badges: {created_count} created, {updated_count} updated."
            )
        )
