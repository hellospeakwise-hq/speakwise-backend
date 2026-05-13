"""Sessions models."""

import uuid

from django.db import models

from base.models import TimeStampedModel


class Track(TimeStampedModel):
    """Track model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    color = models.CharField(max_length=255)
    description = models.TextField()


class SessionVenue(TimeStampedModel):
    """Venue model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    capacity = models.IntegerField()
    location_notes = models.TextField()
    virtual_url = models.URLField(max_length=255)


class Session(TimeStampedModel):
    """Session model."""

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_index=True
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        null=False,
        related_name="event_sessions",
        db_index=True,
    )
    track = models.ForeignKey("Track", on_delete=models.CASCADE)
    title = models.CharField(max_length=255, db_index=True)
    abstract = models.TextField()
    venue = models.ForeignKey("SessionVenue", on_delete=models.CASCADE)
    session_type = models.CharField(max_length=255)
    level = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    max_attendees = models.IntegerField()
    is_draft = models.BooleanField(default=False)  # allow draft sessions

    class Meta:
        """Meta options for Session model."""

        ordering = ("-start_time",)
        unique_together = ("event", "title")
        verbose_name_plural = "Sessions"

    def __str__(self):
        """Str."""
        return self.title


class SessionSponsor(TimeStampedModel):
    """Session sponsor model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        "Session", on_delete=models.CASCADE, null=True, related_name="session_sponsors"
    )
    sponsor = models.CharField(max_length=255)


class SessionSpeaker(TimeStampedModel):
    """Session speaker model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        "Session", on_delete=models.CASCADE, related_name="session_speakers", null=True
    )
    speaker = models.ForeignKey("speakers.SpeakerProfile", on_delete=models.CASCADE)
    role = models.CharField(max_length=255, null=True, blank=True)
