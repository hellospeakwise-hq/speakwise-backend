"""Speaker request service layer."""

import logging

from django.db import transaction

from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest
from speakerrequests.utils import (
    send_request_accepted_email,
    send_request_declined_email,
    send_speaker_request_email,
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
            raise ValueError(
                "A speaker request for this speaker and event already exists."
            )

        request = SpeakerRequest.objects.create(
            organizer=organizer,
            speaker=speaker,
            event=event,
            message=message,
            status=RequestStatusChoices.PENDING,
        )

        # Notify speaker via email
        send_speaker_request_email.enqueue(
            recipient_email=request.speaker.user_account.email,
            event_title=request.event.title,
            message=request.message,
        )
        return request

    @staticmethod
    @transaction.atomic
    def respond_to_request(speaker_request, status_update):
        """Respond to a speaker request (Accept/Reject)."""
        # Ensure only the intended speaker can respond

        print(speaker_request.speaker.user_account.email, speaker_request.event.title)

        if speaker_request.status != RequestStatusChoices.PENDING:
            raise ValueError("Can only respond to pending requests.")

        if status_update not in [
            RequestStatusChoices.ACCEPTED,
            RequestStatusChoices.REJECTED,
        ]:
            raise ValueError("Invalid status update.")

        speaker_request.status = status_update
        speaker_request.save()

        if status_update == RequestStatusChoices.ACCEPTED:
            send_request_accepted_email.enqueue(
                recipient_email=speaker_request.speaker.user_account.email,
                event_title=speaker_request.event.title,
            )
        else:
            send_request_declined_email.enqueue(
                recipeint_email=speaker_request.speaker.user_account.email,
                event_title=speaker_request.event.title,
            )

        return speaker_request

    @staticmethod
    @transaction.atomic
    def create_email_request(request_from, request_to_user, event, message):
        """Create a speaker request for a user not necessarily in the system yet (or via email)."""
        email_request = SpeakerEmailRequests.objects.create(
            request_from=request_from,
            request_to=request_to_user.user_account,
            event=event.title,
            location=event.location.venue,
            message=message,
            status=RequestStatusChoices.PENDING,
        )
        print(email_request.request_to.email)

        if email_request.request_to:
            send_speaker_request_email.enqueue(
                recipient_email=email_request.request_to.email,
                event_title=email_request.event,
                organizer_name=email_request.request_from.username,
                message=email_request.message,
            )

        return email_request

    @staticmethod
    @transaction.atomic
    def respond_to_email_request(request, email_request):
        """Respond to a speaker request (Accept/Reject)."""
        if email_request.status != RequestStatusChoices.PENDING:
            raise ValueError("Can only respond to pending requests.")

        email_request.status = request.data.get("status")
        email_request.save()

        # send email to the user
        if email_request.request_from:
            send_speaker_request_email.enqueue(
                recipient_email=email_request.request_from.email,
                event_title=email_request.event,
                message=email_request.message,
            )

        return email_request
