"""speaker request model."""

import uuid

from django.db import models

from base.models import TimeStampedModel
from speakerrequests.choices import (
    RequestProposedSessionTypeChoices,
    RequestStatusChoices,
)
from speakers.models import SpeakerProfile


class SpeakerRequestQuerySet(models.QuerySet):
    """QuerySet for SpeakerRequests to optimize common queries."""

    def for_organizer(self, user):
        """Requests for organizations where user is a member."""
        return self.none()

    def for_speaker(self, user):
        """Requests sent to this speaker."""
        return self.filter(speaker__user_account=user)

    def with_prefetches(self):
        """Common select_related for optimized fetching."""
        return self.select_related("speaker__user_account", "event")


class SpeakerRequestManager(models.Manager):
    """Manager for SpeakerRequest model."""

    def get_queryset(self):
        """Use custom QuerySet."""
        return SpeakerRequestQuerySet(self.model, using=self._db)

    def for_organizer(self, user):
        """Proxy to QuerySet."""
        return self.get_queryset().for_organizer(user)

    def for_speaker(self, user):
        """Proxy to QuerySet."""
        return self.get_queryset().for_speaker(user)


class SpeakerRequest(TimeStampedModel):
    """speaker request model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects = SpeakerRequestManager()

    speaker = models.ForeignKey(
        SpeakerProfile,
        on_delete=models.CASCADE,
        null=True,
        related_name="requests_received",
    )
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=RequestStatusChoices.choices,
        default=RequestStatusChoices.PENDING,
        db_index=True,
    )
    message = models.TextField(null=False)

    accommodation_covered = models.BooleanField(
        default=False,
        help_text="Whether accommodation is covered by the organizer",
    )
    notes = models.TextField(
        help_text="Internal organizer notes, not visible to the speaker",
        null=True,
    )
    proposed_duration = models.PositiveIntegerField(
        help_text="Proposed duration in minutes",
        null=True,
    )
    proposed_session_type = models.CharField(
        choices=RequestProposedSessionTypeChoices.choices,
        default=RequestProposedSessionTypeChoices.IN_PERSON,
        max_length=50,
    )
    proposed_topic = models.CharField(max_length=255, null=True)
    requested_by = models.ForeignKey(
        SpeakerProfile,
        on_delete=models.CASCADE,
        null=True,
        related_name="requests_made",
    )
    responded_at = models.DateTimeField(null=True)
    response_deadline = models.DateTimeField(
        help_text="Deadline for the speaker to respond to the request",
        null=True,
    )
    response_message = models.TextField(
        help_text="Speaker's response or reason for declining",
        null=True,
    )
    speaker_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Honorarium or fee offered to the speaker, if any",
        null=True,
    )
    travel_covered = models.BooleanField(
        default=False,
        help_text="Whether travel expenses are covered by the organizer",
    )

    class Meta:
        """Meta options for SpeakerRequest."""

        unique_together = ("speaker", "event")
        ordering = ["-created_at"]

    def __str__(self):
        """Str."""
        return f"{self.speaker.user_account.username} request"


class SpeakerEmailRequests(TimeStampedModel):
    """request sent through email."""

    id = models.UUIDField(
        primary_key=True, unique=True, editable=False, default=uuid.uuid4
    )
    event = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    request_from = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="speaker_requests",
    )
    request_to = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
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
