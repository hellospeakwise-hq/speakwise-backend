"""Services that create follower notifications for speaker activity."""

from django.utils import timezone

from events.models import Event
from profiles.models.speaker_models import (
    Notification,
    SpeakerExperiences,
    SpeakerFollow,
    SpeakerProfile,
)
from talks.models import Talks


def _create_follower_notifications(speaker, message, link):
    """Persist a notification for each account following the given speaker."""
    follower_ids = (
        SpeakerFollow.objects.filter(speaker=speaker)
        .values_list("follower_id", flat=True)
        .exclude(follower=speaker.user_account)
    )
    Notification.objects.bulk_create(
        [
            Notification(user_id=user_id, message=message, link=link)
            for user_id in follower_ids
        ],
        batch_size=500,
    )


def notify_followers_of_new_experience(experience_id):
    """Notify followers when a speaker adds a speaking experience."""
    try:
        experience = SpeakerExperiences.objects.select_related(
            "speaker", "speaker__user_account"
        ).get(pk=experience_id)
    except SpeakerExperiences.DoesNotExist:
        return
    if not experience.speaker_id:
        return

    speaker = experience.speaker
    speaker_name = speaker.user_account.get_full_name() or speaker.user_account.username
    topic = experience.topic or experience.event_name or "a new speaking experience"
    _create_follower_notifications(
        speaker,
        f"{speaker_name} added a speaking experience: {topic}.",
        f"/speakers/{speaker.slug}",
    )


def notify_followers_of_upcoming_event(speaker_ids, event_id):
    """Notify followers when speakers are added to a public upcoming event."""
    try:
        event = Event.objects.get(pk=event_id)
    except Event.DoesNotExist:
        return
    if (
        not event.is_active
        or not event.start_date_time
        or event.start_date_time < timezone.now()
    ):
        return

    speakers = SpeakerProfile.objects.filter(pk__in=speaker_ids).select_related(
        "user_account"
    )
    for speaker in speakers:
        speaker_name = (
            speaker.user_account.get_full_name() or speaker.user_account.username
        )
        _create_follower_notifications(
            speaker,
            f"{speaker_name} is speaking at {event.title}.",
            event.get_absolute_url(),
        )


def notify_followers_of_public_talk(talk_id):
    """Notify followers when a speaker's talk becomes public."""
    try:
        talk = Talks.objects.select_related(
            "speaker", "speaker__user_account"
        ).get(pk=talk_id)
    except Talks.DoesNotExist:
        return
    if not talk.is_public:
        return

    speaker = talk.speaker
    speaker_name = speaker.user_account.get_full_name() or speaker.user_account.username
    _create_follower_notifications(
        speaker,
        f"{speaker_name} published a new talk: {talk.title}.",
        f"/speakers/{speaker.slug}",
    )
