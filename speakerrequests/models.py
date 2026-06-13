"""Speaker request model."""

import uuid

from django.db import models

from base.models import TimeStampedModel
from speakerrequests.choices import RequestStatusChoices, SessionTypeChoices
from speakers.models import SpeakerProfile
from users.models import User


class SpeakerRequest(TimeStampedModel):
    """Speaker request model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requested_by = models.ForeignKey(
        "speakers.SpeakerProfile",
        on_delete=models.CASCADE,
        related_name="requests_made",
        null=True,
    )
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    speaker = models.ForeignKey(
        SpeakerProfile,
        on_delete=models.CASCADE,
        related_name="requests_received",
        db_index=True,
    )
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=RequestStatusChoices.choices,
        default=RequestStatusChoices.PENDING,
        db_index=True,
    )
    message = models.TextField(null=False)
    proposed_topic = models.CharField(max_length=255, null=True)
    proposed_session_type = models.CharField(
        max_length=50,
        choices=SessionTypeChoices.choices,
        default=SessionTypeChoices.IN_PERSON,
    )
    proposed_duration = models.PositiveIntegerField(
        null=True, help_text="Proposed duration in minutes"
    )
    speaker_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        help_text="Honorarium or fee offered to the speaker, if any",
    )
    travel_covered = models.BooleanField(
        default=False, help_text="Whether travel expenses are covered by the organizer"
    )
    accommodation_covered = models.BooleanField(
        default=False, help_text="Whether accommodation is covered by the organizer"
    )
    response_message = models.TextField(
        null=True, help_text="Speaker's response or reason for declining"
    )
    responded_at = models.DateTimeField(null=True)
    response_deadline = models.DateTimeField(
        null=True, help_text="Deadline for the speaker to respond to the request"
    )
    notes = models.TextField(
        null=True, help_text="Internal organizer notes, not visible to the speaker"
    )

    class Meta:
        """Meta options for SpeakerRequest."""

        unique_together = ("organization", "speaker", "event")
        ordering = ["-created_at"]

    def __str__(self):
        """Str."""
        return f"{self.speaker.user_account.username} - {self.event} ({self.status})"

    def is_expired(self):
        """Check if the response deadline has passed without a response."""
        from django.utils import timezone

        if self.response_deadline and self.status == RequestStatusChoices.PENDING:
            self.status = RequestStatusChoices.IS_EXPIRED
            self.save(update_fields=["status"])
            return timezone.now() > self.response_deadline
        return False

    def accept(self, response_message=None):
        """Mark the request as accepted by the speaker."""
        from django.utils import timezone

        self.status = RequestStatusChoices.ACCEPTED
        self.responded_at = timezone.now()
        if response_message:
            self.response_message = response_message
        self.save(update_fields=["status", "responded_at", "response_message"])

    def decline(self, response_message=None):
        """Mark the request as declined by the speaker."""
        from django.utils import timezone

        self.status = RequestStatusChoices.DECLINED
        self.responded_at = timezone.now()
        if response_message:
            self.response_message = response_message
        self.save(update_fields=["status", "responded_at", "response_message"])

    def cancel(self, response_message=None):
        """Mark the request as cancelled by the speaker."""
        from django.utils import timezone

        self.status = RequestStatusChoices.CANCELLED
        self.responded_at = timezone.now()
        if response_message:
            self.response_message = response_message
        self.save(update_fields=["status", "responded_at", "response_message"])


class SpeakerEmailRequests(TimeStampedModel):
    """request sent through email."""

    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    event = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    request_from = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="speaker_requests",
    )
    request_to = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="speaker_requests_received",
    )
    message = models.TextField(null=False)
    status = models.CharField(
        max_length=225,
        choices=RequestStatusChoices.choices,
        default=RequestStatusChoices.PENDING,
    )

    def __str__(self):
        """Str."""
        return f"{self.request_from.username} requests {self.request_to.username}"
