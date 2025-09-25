"""Event models."""

from django.db import models
from django.utils import timezone

from base.models import TimeStampedModel
from organizers.models import OrganizerProfile

EVENT_IMAGE_UPLOAD = "event_images/"


class Tag(TimeStampedModel):
    """A model for event tags in the SpeakWise application."""

    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=20, default="#007bff")

    def __str__(self):
        """Return a string representation of the model."""
        return self.name


class Event(TimeStampedModel):
    """A model for events in the SpeakWise application."""

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
    website = models.URLField(max_length=255, blank=True, default="")
    location = models.ForeignKey(
        "Location",
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="event_location",
    )
    start_date_time = models.DateTimeField(default=timezone.now, null=True)
    end_date_time = models.DateTimeField(default=timezone.now, null=True)
    is_active = models.BooleanField(default=False)
    tags = models.ManyToManyField(Tag, related_name="events", blank=True)

    # Add organizer relationship
    organizer = models.ForeignKey(
        OrganizerProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="organized_events",
        help_text="The organizer who created this event",
    )

    def __str__(self):
        """Return a string representation of the model."""
        return self.title


class Location(TimeStampedModel):
    """location models for events."""

    venue = models.CharField(max_length=255, unique=True)
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

    name = models.CharField(max_length=255, null=True)
    code = models.CharField(max_length=255, null=True)

    class Meta:
        """Meta options for the Country model."""

        verbose_name_plural = "Countries"

    def __str__(self):
        """Return a string representation of the model."""
        return self.name
