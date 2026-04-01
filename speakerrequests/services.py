"""Speaker request service layer."""

import logging
from django.db import transaction
from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerRequest, SpeakerEmailRequests
from speakerrequests.utils import (
    send_speaker_request_email,
    send_request_accepted_email,
    send_speaker_request_declined_email,
)

logger = logging.getLogger(__name__)

class SpeakerRequestService:
    """Service class for managing speaker requests."""

    @staticmethod
    @transaction.atomic
    def create_request(organizer, speaker, event, message):
        """Create a new speaker request and notify the speaker."""
        if SpeakerRequest.objects.filter(
            organizer=organizer, speaker=speaker, event=event
        ).exists():
            raise ValueError("A speaker request for this speaker and event already exists.")

        request = SpeakerRequest.objects.create(
            organizer=organizer,
            speaker=speaker,
            event=event,
            message=message,
            status=RequestStatusChoices.PENDING
        )

        # Notify speaker via email
        send_speaker_request_email.enqueue(
            speaker_email=request.speaker.user_account.email,
            event_name=request.event.title,
            organizer_name=request.organizer.name,
            message=request.message,
        )
        return request

    @staticmethod
    @transaction.atomic
    def respond_to_request(request_id, user, status_update):
        """Respond to a speaker request (Accept/Reject)."""
        # Ensure only the intended speaker can respond
        speaker_request = SpeakerRequest.objects.select_related(
            "speaker__user_account", "event", "organizer"
        ).get(pk=request_id, speaker__user_account=user)

        if speaker_request.status != RequestStatusChoices.PENDING:
            raise ValueError("Can only respond to pending requests.")

        if status_update not in [RequestStatusChoices.ACCEPTED, RequestStatusChoices.REJECTED]:
            raise ValueError("Invalid status update.")

        speaker_request.status = status_update
        speaker_request.save()

        if status_update == RequestStatusChoices.ACCEPTED:
            send_request_accepted_email.enqueue(
                speaker=speaker_request.speaker,
                _event=speaker_request.event,
            )
        else:
            send_speaker_request_declined_email.enqueue(
                speaker=speaker_request.speaker,
                _event=speaker_request.event,
            )

        return speaker_request

    @staticmethod
    @transaction.atomic
    def create_email_request(request_from, request_to_user, event_name, location, message):
        """Create a speaker request for a user not necessarily in the system yet (or via email)."""
        email_request = SpeakerEmailRequests.objects.create(
            request_from=request_from,
            request_to=request_to_user,
            event=event_name,
            location=location,
            message=message,
            status=RequestStatusChoices.PENDING
        )

        if email_request.request_to:
            send_speaker_request_email.enqueue(
                speaker_email=email_request.request_to.email,
                event_name=email_request.event,
                organizer_name=email_request.request_from.username,
                message=email_request.message,
            )
        
        return email_request
