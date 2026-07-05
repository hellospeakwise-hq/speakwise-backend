"""Speaker request service layer."""

import logging

from django.db import IntegrityError, transaction

from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest
from speakerrequests.utils import (
    send_request_accepted_email,
<<<<<<< HEAD
    send_speaker_request_declined_email,
=======
    send_request_declined_email,
>>>>>>> 0dcd31b (fix merge conficts and added improvements)
    send_speaker_request_email,
)

logger = logging.getLogger(__name__)


class SpeakerRequestService:
    """Service class for managing speaker requests."""

    @staticmethod
    @transaction.atomic
    def create_request(organizer, speaker, event, message):
        """Create a new speaker request and notify the speaker."""
        try:
            request = SpeakerRequest.objects.create(
                organizer=organizer,
                speaker=speaker,
                event=event,
                message=message,
                status=RequestStatusChoices.PENDING,
            )
        except IntegrityError as err:
            raise ValueError(
                "A speaker request for this speaker and event already exists."
            ) from err

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
        if speaker_request.status != RequestStatusChoices.PENDING:
            raise ValueError("Can only respond to pending requests.")

        if status_update not in [
            RequestStatusChoices.ACCEPTED,
            RequestStatusChoices.REJECTED,
        ]:
            raise ValueError("Invalid status update.")

        speaker_request.status = status_update
        speaker_request.save()

        # send email notifications
        if status_update == RequestStatusChoices.ACCEPTED:
            from events.models import EventSpeakers

            EventSpeakers.objects.get_or_create(
                event=speaker_request.event, speaker=speaker_request.speaker
            )

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
<<<<<<< HEAD
    def create_email_request(
        request_from, request_to_user, event_name, location, message
    ):
=======
    def create_email_request(request_from, request_to_user, event, message):
>>>>>>> 0dcd31b (fix merge conficts and added improvements)
        """Create a speaker request for a user not necessarily in the system yet (or via email)."""
        email_request = SpeakerEmailRequests.objects.create(
            request_from=request_from,
            request_to=request_to_user,  # Changed to accept User instance directly
            event=event.title,
            location=event.location.venue,
            message=message,
            status=RequestStatusChoices.PENDING,
        )
        print(email_request.request_to.email)

        # send email notification
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
    def respond_to_email_request(email_request, status_update):  # Modified signature
        """Respond to a speaker request (Accept/Reject)."""
        if email_request.status != RequestStatusChoices.PENDING:
            raise ValueError("Can only respond to pending requests.")

        if status_update not in [  # Added validation for status_update
            RequestStatusChoices.ACCEPTED,
            RequestStatusChoices.REJECTED,
        ]:
            raise ValueError("Invalid status update.")

        email_request.status = status_update  # Use status_update directly
        email_request.save()

        # send email notification
        if email_request.request_from:
            send_speaker_request_email.enqueue(
                recipient_email=email_request.request_from.email,
                event_title=email_request.event,
                message=email_request.message,
            )

        return email_request
