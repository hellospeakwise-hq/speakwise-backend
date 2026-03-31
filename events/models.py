"""Event models."""

import uuid

from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from base.models import TimeStampedModel

EVENT_IMAGE_UPLOAD = "event_images/"


class Tag(TimeStampedModel):
    """A model for event tags in the SpeakWise application."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=20, default="#007bff")

    def __str__(self):
        """Return a string representation of the model."""
        return self.name


class Event(TimeStampedModel):
    """A model for events in the SpeakWise application."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, unique=True)
    event_nickname = models.CharField(max_length=255, blank=True, default="")
    event_image = models.ImageField(
        "image", upload_to=EVENT_IMAGE_UPLOAD, null=True, blank=True
    )
    short_description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Brief description for event cards",
    )
    description = models.TextField(
        blank=True, default="", help_text="Detailed description for event page"
    )
    website = models.URLField(max_length=255, blank=True, null=True)
    location = models.ForeignKey(
        "Location",
        on_delete=models.SET_NULL,
        null=True,
        related_name="event_location",
    )
    start_date_time = models.DateTimeField(default=timezone.now, null=True)
    end_date_time = models.DateTimeField(default=timezone.now, null=True)
    is_active = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, related_name="events", blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=True)

    # Add organizer relationship
    organizer = models.ForeignKey(
        "organizations.Organization",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="events",
        help_text="The organizer who created this event",
    )

    def get_absolute_url(self):
        """Return the URL to access a particular event instance."""
        return f"/events/{self.slug}/"

    def save(self, *args, **kwargs):
        """Create slug before saving the event."""
        if not self.slug:
            self.slug = slugify(self.title)
        return super().save(*args, **kwargs)

    def __str__(self):
        """Return a string representation of the model."""
        return self.title


class Location(TimeStampedModel):
    """location models for events."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    venue = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    state = models.CharField(max_length=255, blank=True)
    postal_code = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(null=True, max_digits=9, decimal_places=6)
    longitude = models.DecimalField(null=True, max_digits=9, decimal_places=6)
    description = models.TextField(null=True)
    country = models.ForeignKey(
        "Country",
        on_delete=models.CASCADE,
        null=True,
        related_name="location_country",
    )

    def __str__(self):
        """Return a string representation of the model."""
        return self.venue


class Country(TimeStampedModel):
    """A model for countries in the SpeakWise application."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, null=True, unique=True)
    code = models.CharField(max_length=255, null=True, unique=True)

    class Meta:
        """Meta options for the Country model."""

        verbose_name_plural = "Countries"

    def __str__(self):
        """Return a string representation of the model."""
        return self.name


class EventSpeakers(TimeStampedModel):
    """Event speakers model."""

    speaker = models.ForeignKey("speakers.SpeakerProfile", on_delete=models.CASCADE)
    event = models.ForeignKey("Event", on_delete=models.CASCADE)
    has_spoken = models.BooleanField(default=False)

    def __str__(self):
        """Return a string representation of the model."""
        return f"{self.speaker.user_account.username} - {self.event.title}"
