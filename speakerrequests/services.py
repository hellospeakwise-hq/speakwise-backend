"""Business logic for speaker requests."""

from base.constants import FRONTEND_URL
from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerRequest
from speakerrequests.tasks import (
    send_request_accepted_email,
    send_request_declined_email,
    send_speaker_deck_upload_email,
    send_speaker_email_request_email,
    send_speaker_org_request_email,
)
from speakers.models import Notification


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

    upload_url = f"{FRONTEND_URL}/events/{event.slug}/upload-deck"

    notifications_to_create = []
    for speaker_request in accepted_requests:
        user = speaker_request.speaker.user_account

        notifications_to_create.append(
            Notification(
                recipient=speaker_request.speaker,
                title=f"Upload your presentation for {event.title}",
                message=(
                    f"The organizer has enabled presentation uploads for "
                    f"'{event.title}'. Please upload your speaker deck."
                ),
                link=upload_url,
            )
        )

        send_speaker_deck_upload_email.enqueue(
            speaker_email=user.email,
            event_name=event.title,
            upload_url=upload_url,
        )

    if notifications_to_create:
        Notification.objects.bulk_create(notifications_to_create)


def notify_speaker_of_org_request(data) -> None:
    """Notify a speaker that they have received a speaking request from an organization."""
    send_speaker_org_request_email.enqueue(
        speaker_name=data.speaker.user_account.username,
        event_name=data.event.title,
        organization_name=data.organization.name,
        organizer_name=data.requested_by.user_account.username,
        message=data.message,
        request_id=str(data.id),
        recipient_email=data.speaker.user_account.email,
    )


def notify_speaker_email_request(data) -> None:
    """Notify a speaker that they have received a speaking request."""
    send_speaker_email_request_email.enqueue(
        speaker_name=data.request_to.username,
        event_name=data.event,
        message=data.message,
        request_id=str(data.id),
        requester_name=data.request_from.username,
        requester_email=data.request_from.email,
        event_location=data.location,
    )


def notify_speaker_reqest_accepted(data) -> None:
    """Notify the requester that their speaking request has been accepted by the speaker."""
    send_request_accepted_email.enqueue(
        speaker_name=data.speaker.user_account.username,
        event_name=data.event.title,
        requester_name=data.requested_by.user_account.username,
        requester_email=data.requested_by.user_account.email,
    )


def notify_speaker_reqest_declined(data) -> None:
    """Notify the requester that their speaking request has been declined by the speaker."""
    send_request_declined_email.enqueue(
        speaker_name=data.speaker.user_account.username,
        event_name=data.event.title,
        requester_name=data.requested_by.user_account.username,
        requester_email=data.requested_by.user_account.email,
    )
