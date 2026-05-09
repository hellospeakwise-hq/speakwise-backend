"""Models for the feedback app."""

# Create your models here.
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from base.models import TimeStampedModel
from speakers.models import SpeakerProfile

RATING_VALIDATORS = [MinValueValidator(1), MaxValueValidator(10)]


class Feedback(TimeStampedModel):
    """Feedback model for storing user feedback."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    speaker = models.ForeignKey(
        SpeakerProfile,
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="speaker_feedback",
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.DO_NOTHING,
        null=True,
        blank=True,
        related_name="event_feedback",
    )
    overall_rating = models.IntegerField(
        validators=RATING_VALIDATORS,
        error_messages={"error": "value should be an integer of value 1-10"},
    )
    engagement = models.IntegerField(
        validators=RATING_VALIDATORS,
        error_messages={"error": "value should be an integer of value 1-10"},
    )
    clarity = models.IntegerField(
        validators=RATING_VALIDATORS,
        error_messages={"error": "value should be an integer of value 1-10"},
    )
    content_depth = models.IntegerField(
        validators=RATING_VALIDATORS,
        error_messages={"error": "value should be an integer of value 1-10"},
    )
    speaker_knowledge = models.IntegerField(
        validators=RATING_VALIDATORS,
        error_messages={"error": "value should be an integer of value 1-10"},
    )
    practical_relevance = models.IntegerField(
        validators=RATING_VALIDATORS,
        error_messages={"error": "value should be an integer of value 1-10"},
    )
    comments = models.TextField(max_length=2000, blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)
    is_attendee = models.BooleanField(default=False)

    class Meta:
        """Meta options for Feedback model."""

        db_table = "feedbacks"
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ["-created_at"]

    def __str__(self):
        """Return string representation."""
        return f"Feedback for {self.speaker} with overall rating {self.overall_rating}"


class SpeakerFeedbackSettings(TimeStampedModel):
    """Per-event feedback toggle controlled by the speaker."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    speaker = models.ForeignKey(
        SpeakerProfile,
        on_delete=models.CASCADE,
        related_name="feedback_settings",
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="speaker_feedback_settings",
    )
    feedback_enabled = models.BooleanField(default=True)

    class Meta:
        """Meta options for SpeakerFeedbackSettings."""

        db_table = "speaker_feedback_settings"
        unique_together = ("speaker", "event")

    def __str__(self):
        """Return string representation."""
        state = "enabled" if self.feedback_enabled else "disabled"
        return f"Feedback {state} for {self.speaker} at {self.event}"
