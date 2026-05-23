"""events utils."""

from django.http import Http404
from django.conf import settings

from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerRequest
from speakerrequests.tasks import send_speaker_deck_upload_email
from speakers.models import Notification

from organizations.models import Organization, OrganizationMembership


def create_event_payload(request):
    """Create event payload."""
    try:
        user = request.user
        membership = OrganizationMembership.objects.get(user=user)
        if membership.is_admins() or membership.is_organizers():
            organization = membership.organization
        else:
            raise Http404("User does not have permission to create an event.")
    except Organization.DoesNotExist as err:
        raise Http404("User does not belong to any organization.") from err
    except OrganizationMembership.DoesNotExist as err:
        raise Http404("User is not a member of the organization.") from err

    payload = request.data.copy()
    payload["organizer"] = organization.id
    return payload


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
                recipient=user,
                title=f"Upload your presentation for {event.title}",
                message=(
                    f"The organizer has enabled presentation uploads for "
                    f"'{event.title}'. Please upload your speaker deck."
                ),
                link=upload_url,
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
