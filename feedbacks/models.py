"""Models for the feedback app."""

# Create your models here.
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from base.models import TimeStampedModel

RATING_VALIDATORS = [MinValueValidator(1), MaxValueValidator(10)]

RATING_FIELDS = (
    "overall_rating",
    "engagement",
    "clarity",
    "content_depth",
    "speaker_knowledge",
    "practical_relevance",
)


class Feedback(TimeStampedModel):
    """Feedback model for storing user feedback."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    speaker = models.ForeignKey(
        "profiles.SpeakerProfile",
        on_delete=models.SET_NULL,
        null=True,
        related_name="speaker_feedback",
    )
    experience = models.ForeignKey(
        "profiles.SpeakerExperiences",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feedback",
        help_text="The presentation the feedback was given for.",
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
    name = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Optional public name of the person giving feedback.",
    )
    is_anonymous = models.BooleanField(default=False)
    submitter_ip_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Salted hash of the submitter's IP used for rate limiting.",
    )

    class Meta:
        """Meta options for Feedback model."""

        db_table = "feedbacks"
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        """Derive anonymity from the name field before saving."""
        self.is_anonymous = not bool(self.name.strip())
        return super().save(*args, **kwargs)

    def __str__(self):
        """Return string representation."""
        return f"Feedback for {self.speaker} with overall rating {self.overall_rating}"
