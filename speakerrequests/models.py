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
        org_ids = OrganizationMembership.objects.filter(user=user).values_list(
            "organization_id", flat=True
        )
        return self.filter(organizer_id__in=org_ids)

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

    def for_event(self, event):
        """Proxy to QuerySet."""
        return self.get_queryset().filter(event=event)


class SpeakerRequest(TimeStampedModel):
    """speaker request model."""

    objects = SpeakerRequestManager()

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
