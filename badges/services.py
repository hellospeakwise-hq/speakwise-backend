"""Services for evaluating and managing speaker badges."""

import logging

from django.db.models import Avg

from badges.choices import BadgeStatusChoices, BadgeTierChoices
from badges.models import BadgeDefinition, SpeakerBadge
from feedbacks.models import Feedback
from profiles.models.speaker_models import (
    Notification,
    SpeakerExperiences,
    SpeakerProfile,
)
from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerRequest

logger = logging.getLogger(__name__)

DEFAULT_BADGE_DEFINITIONS = [
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


def ensure_badge_definitions() -> None:
    """Ensure predefined badge catalog exists in the database."""
    if BadgeDefinition.objects.count() < len(DEFAULT_BADGE_DEFINITIONS):
        for item in DEFAULT_BADGE_DEFINITIONS:
            BadgeDefinition.objects.update_or_create(
                token_id=item["token_id"],
                defaults=item,
            )


def evaluate_speaker_badges(speaker: SpeakerProfile) -> list[SpeakerBadge]:
    """Evaluate all badge criteria for a given speaker profile.

    Unlocks badges to 'eligible' status if criteria are satisfied.
    Does NOT downgrade 'claimed' badges.
    """
    if not speaker:
        return []

    # Ensure catalog is available
    ensure_badge_definitions()

    # 1. Compute speaker metrics
    talks_count = SpeakerExperiences.objects.filter(speaker=speaker).count()

    requests_accepted_count = SpeakerRequest.objects.filter(
        speaker=speaker,
        status=RequestStatusChoices.ACCEPTED,
    ).count()

    feedbacks_count = Feedback.objects.filter(speaker=speaker).count()

    avg_rating_dict = Feedback.objects.filter(speaker=speaker).aggregate(
        avg_rating=Avg("overall_rating")
    )
    avg_rating = avg_rating_dict["avg_rating"] or 0.0

    # 2. Iterate through all badge definitions
    unlocked_badges = []
    badge_definitions = BadgeDefinition.objects.all()

    for badge in badge_definitions:
        speaker_badge, created = SpeakerBadge.objects.get_or_create(
            speaker=speaker,
            badge=badge,
            defaults={"status": BadgeStatusChoices.LOCKED},
        )

        # Never overwrite a badge that has already been claimed on-chain
        if speaker_badge.status == BadgeStatusChoices.CLAIMED:
            continue

        is_eligible = False

        if badge.metric_type == "talks_count":
            is_eligible = talks_count >= badge.metric_threshold
        elif badge.metric_type == "requests_count":
            is_eligible = requests_accepted_count >= badge.metric_threshold
        elif badge.metric_type == "feedbacks_count":
            is_eligible = feedbacks_count >= badge.metric_threshold
        elif badge.metric_type == "rating_avg":
            # Rating requirement needs at least 3 feedbacks
            is_eligible = (feedbacks_count >= 3) and (
                avg_rating >= float(badge.metric_threshold)
            )

        if is_eligible and speaker_badge.status == BadgeStatusChoices.LOCKED:
            speaker_badge.status = BadgeStatusChoices.ELIGIBLE
            speaker_badge.save(update_fields=["status", "updated_at"])
            unlocked_badges.append(speaker_badge)

            # Send in-app notification to the speaker
            try:
                Notification.objects.create(
                    user=speaker.user_account,
                    message=f"🎉 You've unlocked the '{badge.name}' Web3 Badge! Claim your Soulbound credential on Base.",
                    link=f"/speakers/{speaker.slug}?tab=badges",
                )
            except Exception as e:
                logger.warning(
                    f"Could not create notification for badge {badge.name}: {e}"
                )

    return unlocked_badges
