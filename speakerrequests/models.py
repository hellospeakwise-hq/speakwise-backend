"""speaker request model."""

import uuid

from django.db import models

from base.models import TimeStampedModel
from organizations.models import OrganizationMembership
from speakerrequests.choices import RequestStatusChoices
from speakers.models import SpeakerProfile
from users.models import User


class SpeakerRequestQuerySet(models.QuerySet):
    """QuerySet for SpeakerRequests to optimize common queries."""

    def for_organizer(self, user):
        """Requests for organizations where user is a member."""
        return self.filter(organizer__organization_memberships__user=user)

    def for_speaker(self, user):
        """Requests sent to this speaker."""
        return self.filter(speaker__user_account=user)

    def with_prefetches(self):
        """Common select_related for optimized fetching."""
        return self.select_related("organizer", "speaker__user_account", "event")


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

    def with_prefetches(self):
        """Proxy to QuerySet."""
        return self.get_queryset().with_prefetches()


class SpeakerRequest(TimeStampedModel):
    """speaker request model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects = SpeakerRequestManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects = SpeakerRequestManager()

    organizer = models.ForeignKey(
        "organizations.Organization", on_delete=models.CASCADE
    )
    speaker = models.ForeignKey(SpeakerProfile, on_delete=models.CASCADE)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE)
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
        on_delete=models.SET_NULL,
        null=True,
        related_name="speaker_requests",
    )
    request_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="speaker_requests_received",
    )
    message = models.TextField(null=False)
    status = models.CharField(
        max_length=20,
        choices=RequestStatusChoices.choices,
        default=RequestStatusChoices.PENDING,
    )

    def __str__(self):
        """Str."""
        return f"{self.request_from.username} requests {self.request_to.username}"
