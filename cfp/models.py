"""CFP models."""

import uuid

from django.conf import settings
from django.db import models

from base.models import TimeStampedModel
from cfp.choices import AudienceLevelChoices, CFPStatusChoices, TalkTypeChoices
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
    talk_type = models.CharField(max_length=20, choices=TalkTypeChoices.choices)
    audience = models.CharField(max_length=20, choices=AudienceLevelChoices.choices)
    category = models.CharField(max_length=100, choices=TalkCategoryChoices.choices)
    elevator_pitch = models.CharField(
        max_length=300, help_text="A short summary of your talk (max 300 characters)."
    )
    abstract = models.TextField(help_text="Full description of your talk.")
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
    other_comments = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=CFPStatusChoices.choices,
        default=CFPStatusChoices.PENDING,
    )

    class Meta:
        unique_together = ("event", "submitter")
        verbose_name = "CFP Submission"
        verbose_name_plural = "CFP Submissions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.submitter} — {self.event.title}"
