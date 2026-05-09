"""CFP models."""

import uuid

from django.conf import settings
from django.db import models

from base.models import TimeStampedModel
from cfps.choices import (
    AudienceLevelChoices,
    CFPStatusChoices,
    TalkDurationChoices,
    TalkTypeChoices,
)
from events.models import Event
from speakers.models import SpeakerProfile
from talks.choices import TalkCategoryChoices


class CFPSubmission(TimeStampedModel):
    """Call For Papers submission model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="cfp_submissions"
    )
    submitter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cfp_submissions",
    )
    title = models.CharField(
        max_length=200, help_text="Title of your talk.", default=""
    )
    talk_type = models.CharField(max_length=20, choices=TalkTypeChoices.choices)
    duration = models.IntegerField(
        choices=TalkDurationChoices.choices,
        null=True,
        blank=True,
        help_text="Expected talk duration in minutes.",
    )
    audience = models.CharField(max_length=20, choices=AudienceLevelChoices.choices)
    category = models.CharField(max_length=100, choices=TalkCategoryChoices.choices)
    language = models.CharField(
        max_length=50,
        default="English",
        help_text="Language the talk will be delivered in.",
        blank=True,
    )
    elevator_pitch = models.CharField(
        max_length=300, help_text="A short summary of your talk (max 300 characters)."
    )
    abstract = models.TextField(help_text="Full description of your talk.")
    outline = models.TextField(
        blank=True,
        default="",
        help_text="Private structured outline of your talk (only visible to organizers).",
    )
    slides_url = models.URLField(
        blank=True,
        null=True,
        help_text="Link to draft slides or a previous version.",
    )
    recording_url = models.URLField(
        blank=True,
        null=True,
        help_text="Link to a recording of this talk at a previous event.",
    )
    co_speakers = models.ManyToManyField(
        SpeakerProfile,
        blank=True,
        related_name="co_speaker_cfp_submissions",
        help_text="Registered co-presenters.",
    )
    other_speakers_text = models.TextField(
        blank=True,
        default="",
        help_text="Names/emails of co-presenters not yet on SpeakWise.",
    )
    notes_for_organizers = models.TextField(
        blank=True,
        default="",
        help_text="Private notes only visible to organizers.",
    )
    other_comments = models.TextField(blank=True, default="")
    is_first_time_speaker = models.BooleanField(
        default=False,
        help_text="Is this your first time speaking at a conference?",
    )
    travel_support_needed = models.BooleanField(
        default=False,
        help_text="Do you need travel or accommodation support?",
    )
    status = models.CharField(
        max_length=20,
        choices=CFPStatusChoices.choices,
        default=CFPStatusChoices.PENDING,
    )

    class Meta:
        """Meta options for CFPSubmission."""

        verbose_name = "CFP Submission"
        verbose_name_plural = "CFP Submissions"
        ordering = ["-created_at"]

    @property
    def organizer(self):
        """Return the organization that owns the event this submission belongs to."""
        return self.event.organizer

    def __str__(self):
        """Return string representation of the submission."""
        return f"{self.submitter} — {self.title}"
