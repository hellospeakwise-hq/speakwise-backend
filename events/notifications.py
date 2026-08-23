"""Event notification utilities."""

from django.conf import settings

from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerRequest
from speakerrequests.tasks import send_speaker_deck_upload_email
from speakers.models import Notification, SpeakerProfile


def notify_accepted_speakers_deck_upload(event):
    """Send email + in-app notifications to all accepted speakers for an event.

    Called when an organizer enables speaker deck uploads for the event.

    Args:
        event: The Event instance with speaker_deck_upload_enabled=True.
    """
    accepted_requests = SpeakerRequest.objects.filter(
        event=event,
        status=RequestStatusChoices.ACCEPTED,
    ).select_related("speaker__user_account")

    upload_url = f"{settings.FRONTEND_URL}/events/{event.slug}/upload-deck"

    notifications_to_create = []
    for speaker_request in accepted_requests:
        user = speaker_request.speaker.user_account

        # Create in-app notification
        notifications_to_create.append(
            Notification(
                user=user,
                message=(
                    f"The organizer has enabled presentation uploads for "
                    f"'{event.title}'. Please upload your speaker deck."
                ),
            )
        )

        # Enqueue email notification
        send_speaker_deck_upload_email.enqueue(
            speaker_email=user.email,
            event_name=event.title,
            upload_url=upload_url,
        )

    # Bulk-create all in-app notifications
    if notifications_to_create:
        Notification.objects.bulk_create(notifications_to_create)


def notify_if_cfp_just_published(event, *, was_open):
    """Notify matching speakers when a CFP transitions from closed to open."""
    if event.cfp_open and not was_open:
        notify_speakers_matching_published_cfp(event)


def notify_speakers_matching_published_cfp(event):
    """Notify speakers whose skills overlap this event's CFP tags.

    Event tags are treated as CFP skill/topic tags. Speakers with no overlapping
    skills are not notified.
    """
    from cfps.tasks import send_cfp_skill_match_email

    skill_names = list(event.tags.values_list("name", flat=True))
    speakers = SpeakerProfile.objects.matching_skill_names(
        skill_names
    ).prefetch_related("skill_tags")

    seen_user_ids = set()
    notifications_to_create = []
    cfp_url = f"{settings.FRONTEND_URL}/events/{event.slug}"

    for speaker in speakers:
        user = speaker.user_account
        if user.id in seen_user_ids:
            continue
        seen_user_ids.add(user.id)

        speaker_skills = {
            tag.name.strip().lower()
            for tag in speaker.skill_tags.all()
            if tag.name and tag.name.strip()
        }
        matched_skills = [
            name
            for name in skill_names
            if name and name.strip().lower() in speaker_skills
        ]
        skills = ", ".join(matched_skills)
        message = (
            f"A new CFP for '{event.title}' matches your skills ({skills}). "
            f"You can submit a talk while the CFP is open."
        )
        notifications_to_create.append(Notification(user=user, message=message))
        if user.email:
            send_cfp_skill_match_email.enqueue(
                speaker_email=user.email,
                speaker_name=user.first_name or user.username,
                event_name=event.title,
                cfp_url=cfp_url,
                matched_skills=skills,
            )

    if notifications_to_create:
        Notification.objects.bulk_create(notifications_to_create)
