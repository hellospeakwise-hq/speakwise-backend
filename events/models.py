"""Event models."""

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from base.models import TimeStampedModel
from events.utils import normalize_event_website

EVENT_IMAGE_UPLOAD = "event_images/"


class EventQuerySet(models.QuerySet):
    """QuerySet for published, pending, duplicate, and CFP event lookups."""

    def find_duplicate(self, title, website, exclude_id=None):
        """Return an event with the same title and official website, if any."""
        qs = self.filter(title__iexact=title.strip())
        if exclude_id is not None:
            qs = qs.exclude(pk=exclude_id)
        normalized = normalize_event_website(website)
        for event in qs.only("id", "website", "title"):
            if normalize_event_website(event.website or "") == normalized:
                return event
        return None

    def with_open_cfp(self):
        """Return active events whose CFP is currently open.

        Open requires the manual cfp_open flag, and must fall within the
        optional open_date / deadline window.
        """
        now = timezone.now()
        return self.filter(
            is_active=True,
            cfp_open=True,
        ).filter(
            Q(cfp_open_date__isnull=True) | Q(cfp_open_date__lte=now),
            Q(cfp_deadline__isnull=True) | Q(cfp_deadline__gte=now),
        )

    def with_expired_cfp(self):
        """Return events still marked open whose CFP deadline has passed.

        Intended for the periodic job that closes expired CFPs; the manual
        cfp_open flag is the only guard, so events that have not been saved
        since their deadline passed are still caught here.
        """
        return self.filter(
            cfp_open=True,
            cfp_deadline__isnull=False,
            cfp_deadline__lt=timezone.now(),
        )


class EventManager(models.Manager.from_queryset(EventQuerySet)):
    """Manager for Event with listing and CFP queryset helpers."""


class Event(TimeStampedModel):
    """A model for events in the SpeakWise application."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, unique=True, help_text="Event title")
    event_nickname = models.CharField(max_length=255, blank=True, default="")
    event_image = models.ImageField(
        "image", upload_to=EVENT_IMAGE_UPLOAD, null=True, blank=True
    )
    description = models.TextField(
        blank=True, default="", help_text="Detailed description for event page"
    )
    website = models.URLField(
        max_length=255,
        help_text=(
            "Official event website or a public page about the event "
            "(for example a LinkedIn post)."
        ),
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submitted_events",
        help_text=(
            "The user who submitted this event for listing. Null for listings "
            "created before attribution existed, and if the submitter account "
            "is later deleted."
        ),
    )
    start_date_time = models.DateTimeField(default=timezone.now, null=True)
    end_date_time = models.DateTimeField(default=timezone.now, null=True)
    is_active = models.BooleanField(default=False, db_index=True)
    slug = models.SlugField(max_length=255, null=True)
    location = models.CharField(max_length=150, null=True, blank=True)

    # CFP configuration
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

    objects = EventManager()

    class Meta:
        """Meta options for the Event model."""

        verbose_name = "Event"
        verbose_name_plural = "Events"

    def get_absolute_url(self):
        """Return the URL to access a particular event instance."""
        return f"/events/{self.slug}/"

    @property
    def is_cfp_currently_open(self) -> bool:
        """Whether this event's CFP is open right now.

        Requires the manual cfp_open flag, and must fall within the
        optional open_date / deadline window.
        """
        if not self.cfp_open:
            return False
        now = timezone.now()
        if self.cfp_open_date and now < self.cfp_open_date:
            return False
        return not (self.cfp_deadline and now > self.cfp_deadline)

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
        return f"{self.title} {self.submitted_by.username}"
