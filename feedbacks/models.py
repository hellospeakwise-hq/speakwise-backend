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
    # Nullable at the database level only for feedback that predates
    # event-scoping; new submissions must provide it (enforced in the serializer).
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedbacks",
        help_text="The event the feedback was given at.",
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


class EventFeedbackPreferenceManager(models.Manager):
    """Manage event-scoped speaker feedback preferences."""

    def is_enabled_for(self, speaker, event):
        """Return whether feedback is enabled for a speaker at an event."""
        preference = self.filter(speaker=speaker, event=event).first()
        return preference is None or preference.is_feedback_enabled

    def set_for(self, speaker, event, is_feedback_enabled):
        """Create or update a speaker's feedback preference for an event."""
        preference, _ = self.update_or_create(
            speaker=speaker,
            event=event,
            defaults={"is_feedback_enabled": is_feedback_enabled},
        )
        return preference


class EventFeedbackPreference(TimeStampedModel):
    """A speaker's choice to accept or close feedback for a specific event.

    Absence of a record means feedback is open — speakers only opt out.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    objects = EventFeedbackPreferenceManager()
    speaker = models.ForeignKey(
        SpeakerProfile,
        on_delete=models.CASCADE,
        related_name="event_feedback_preferences",
    )
    event = models.ForeignKey(
        "events.Event",
        on_delete=models.CASCADE,
        related_name="speaker_feedback_preferences",
    )
    is_feedback_enabled = models.BooleanField(
        default=True,
        help_text="Whether the speaker accepts feedback for this event.",
    )

    class Meta:
        """Meta options for EventFeedbackPreference model."""

        db_table = "event_feedback_preferences"
        verbose_name = "Event Feedback Preference"
        verbose_name_plural = "Event Feedback Preferences"
        unique_together = ("speaker", "event")
        ordering = ["-created_at"]

    def __str__(self):
        """Return string representation."""
        state = "enabled" if self.is_feedback_enabled else "disabled"
        return f"Feedback {state} for {self.speaker} at {self.event}"
