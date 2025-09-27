"""Models for the feedback app."""

from django.db import models

# Create your models here.
from base.models import TimeStampedModel
from talks.models import Session


class Feedback(TimeStampedModel):
    """Feedback model for storing user feedback."""

    session = models.ForeignKey(
        Session, on_delete=models.CASCADE, related_name="session_feedbacks"
    )
    attendee = models.ForeignKey(
        "attendees.AttendeeProfile",
        on_delete=models.CASCADE,
        related_name="attendee_feedbacks",
    )
    overall_rating = models.IntegerField()
    engagement = models.IntegerField()
    clarity = models.IntegerField()
    content_depth = models.IntegerField()
    speaker_knowledge = models.IntegerField()
    practical_relevance = models.IntegerField()
    comments = models.TextField(max_length=2000, blank=True, null=True)
    is_anonymous = models.BooleanField(default=False)

    class Meta:
        """Meta options for Feedback model."""

        db_table = "feedbacks"
        verbose_name = "Feedback"
        verbose_name_plural = "Feedbacks"
        ordering = ["-created_at"]

    def __str__(self):
        """Return string representation."""
        if self.is_anonymous:
            return f"Anonymous Feedback #{self.pk}"
        return f"Feedback #{self.pk} by {self.attendee}"
