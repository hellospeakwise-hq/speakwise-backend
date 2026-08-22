"""Event models."""

import uuid

from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from base.models import TimeStampedModel

EVENT_IMAGE_UPLOAD = "event_images/"


class Tag(TimeStampedModel):
    """A model for event tags in the SpeakWise application."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=20, default="#007bff")

    def __str__(self):
        """Return a string representation of the model."""
        return self.name


class EventQuerySet(models.QuerySet):
    """QuerySet helpers for Event CFP visibility."""

    def with_open_cfp(self):
        """Return active events whose CFP is currently open.

        Open requires accepts_cfp and cfp_open, and must fall within the
        optional open_date / deadline window.
        """
        now = timezone.now()
        return self.filter(
            is_active=True,
            accepts_cfp=True,
            cfp_open=True,
        ).filter(
            Q(cfp_open_date__isnull=True) | Q(cfp_open_date__lte=now),
            Q(cfp_deadline__isnull=True) | Q(cfp_deadline__gte=now),
        )


class EventManager(models.Manager):
    """Manager for Event with CFP queryset helpers."""

    def get_queryset(self):
        """Use EventQuerySet."""
        return EventQuerySet(self.model, using=self._db)

    def with_open_cfp(self):
        """Proxy to EventQuerySet.with_open_cfp."""
        return self.get_queryset().with_open_cfp()


class Event(TimeStampedModel):
    """A model for events in the SpeakWise application."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
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
    is_active = models.BooleanField(default=False, db_index=True)
    tags = models.ManyToManyField(Tag, related_name="events", blank=True)
    slug = models.SlugField(max_length=255, null=True)

    # CFP configuration
    accepts_cfp = models.BooleanField(
        default=False,
        help_text="Does this event accept Call for Papers submissions?",
    )
    cfp_open = models.BooleanField(
        default=False,
        help_text="Is the CFP currently open for submissions?",
    )
    cfp_link = models.URLField(
        max_length=255,
        blank=True,
        default="",
        help_text="External URL for the event's CFP page.",
    )
    cfp_description = models.TextField(
        blank=True,
        default="",
        help_text="What the organizers are looking for — shown to speakers on the CFP page.",
    )
    cfp_open_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When CFP submissions open.",
    )
    cfp_deadline = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When CFP submissions close.",
    )
    cfp_speaker_notification_date = models.DateField(
        null=True,
        blank=True,
        help_text="When speakers will be notified of the outcome.",
    )

    speaker_deck_upload_enabled = models.BooleanField(
        default=False,
        help_text="When enabled, accepted speakers can upload their presentation materials.",
    )

    objects = EventManager()

    def get_absolute_url(self):
        """Return the URL to access a particular event instance."""
        return f"/events/{self.slug}/"

    @property
    def is_cfp_currently_open(self) -> bool:
        """Whether this event's CFP is open right now.

        Requires accepts_cfp and the manual cfp_open flag, and must fall
        within the optional open_date / deadline window.
        """
        if not self.accepts_cfp or not self.cfp_open:
            return False
        now = timezone.now()
        if self.cfp_open_date and now < self.cfp_open_date:
            return False
        if self.cfp_deadline and now > self.cfp_deadline:
            return False
        return True

    def save(self, *args, **kwargs):
        """Create slug and mark expired CFPs closed before saving."""
        if not self.slug:
            self.slug = slugify(self.title)
        # Persist closed status when the deadline has passed.
        if self.cfp_open and self.cfp_deadline and timezone.now() > self.cfp_deadline:
            self.cfp_open = False
        return super().save(*args, **kwargs)

    def __str__(self):
        """Return a string representation of the model."""
        return self.title


class EventSpeakers(TimeStampedModel):
    """Speakers who have spoken or are scheduled at an event."""

    created_at = models.DateTimeField(default=timezone.now)
    has_spoken = models.BooleanField(default=False)
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
    )
    speaker = models.ForeignKey(
        "speakers.SpeakerProfile",
        on_delete=models.CASCADE,
    )

    class Meta:
        """Meta options for EventSpeakers."""

        verbose_name = "Event Speaker"
        verbose_name_plural = "Event Speakers"

    def __str__(self):
        """Return a string representation of the model."""
        return f"{self.speaker} at {self.event}"


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
    name = models.CharField(max_length=100, null=True, unique=True)
    code = models.CharField(max_length=2, null=True, unique=True)

    class Meta:
        """Meta options for the Country model."""

        verbose_name_plural = "Countries"

    def __str__(self):
        """Return a string representation of the model."""
        return self.name
