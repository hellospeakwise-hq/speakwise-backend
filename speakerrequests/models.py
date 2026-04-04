"""speaker request model."""

import uuid

from django.db import models

from base.models import TimeStampedModel
from speakerrequests.choices import RequestStatusChoices
from speakers.models import SpeakerProfile
from users.models import User


class SpeakerRequest(TimeStampedModel):
    """speaker request model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organizer = models.ForeignKey(
        "organizations.Organization", on_delete=models.DO_NOTHING
    )
    speaker = models.ForeignKey(SpeakerProfile, on_delete=models.DO_NOTHING)
    event = models.ForeignKey("events.Event", on_delete=models.DO_NOTHING)
    status = models.CharField(
        max_length=10,
        choices=RequestStatusChoices.choices,
        default=RequestStatusChoices.PENDING,
    )
    message = models.TextField(null=False)

    class Meta:
        """Meta options for SpeakerRequest."""

        unique_together = ("organizer", "speaker", "event")
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
