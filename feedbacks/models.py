"""Models for the feedback app."""

from django.db import models

# Create your models here.
from base.models import TimeStampedModel
from speakers.models import SpeakerProfile

RATE_VALIDATION_REGEX = []


class Feedback(TimeStampedModel):
    """Feedback model for storing user feedback."""

    speaker = models.ForeignKey(
        SpeakerProfile,
        on_delete=models.DO_NOTHING,
        null=True,
        related_name="speaker_feedback",
    )
    overall_rating = models.IntegerField(
        validators=RATE_VALIDATION_REGEX,
        error_messages={"error": "value should be an integer of value 1-10"},
    )
    engagement = models.IntegerField(
        validators=RATE_VALIDATION_REGEX,
        error_messages={"error": "value should be an integer of value 1-10"},
    )
    clarity = models.IntegerField(
        validators=RATE_VALIDATION_REGEX,
        error_messages={"error": "value should be an integer of value 1-10"},
    )
    content_depth = models.IntegerField(
        validators=RATE_VALIDATION_REGEX,
        error_messages={"error": "value should be an integer of value 1-10"},
    )
    speaker_knowledge = models.IntegerField(
        validators=RATE_VALIDATION_REGEX,
        error_messages={"error": "value should be an integer of value 1-10"},
    )
    practical_relevance = models.IntegerField(
        validators=RATE_VALIDATION_REGEX,
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
