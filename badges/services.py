"""Services for evaluating and managing speaker badges."""

import logging

from django.db.models import Avg

from badges.models import BadgeDefinition, BadgeStatusChoices, SpeakerBadge
from feedbacks.models import Feedback
from profiles.models.speaker_models import (
    Notification,
    SpeakerExperiences,
    SpeakerProfile,
)
from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerRequest

logger = logging.getLogger(__name__)


def evaluate_speaker_badges(speaker: SpeakerProfile) -> list[SpeakerBadge]:
    """Evaluate all badge criteria for a given speaker profile.

    Unlocks badges to 'eligible' status if criteria are satisfied.
    Does NOT downgrade 'claimed' badges.
    """
    if not speaker:
        return []

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
