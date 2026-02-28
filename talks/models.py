"""talks models."""

import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from base.models import TimeStampedModel
from events.models import Event
from speakers.models import SpeakerProfile
from talks.choices import TalkCategoryChoices

PRESENTATION_FILES_UPLOAD_DIR = "presentation_files"


class Session(TimeStampedModel):
    """talk session model."""

    type = models.CharField(
        max_length=255, help_text="session type. eg. Keynote, lightning talk. etc"
    )
    duration = models.IntegerField(help_text="session duration in minutes")
    talk = models.ForeignKey(
        "Talks", on_delete=models.CASCADE, related_name="talk_sessions"
    )

    def __str__(self):
        """String rep of speakwise social."""
        return self.talk.title


class Talks(TimeStampedModel):
    """Talks model."""

    title = models.CharField(max_length=255)
    description = models.TextField()
    speaker = models.ForeignKey(
        SpeakerProfile, on_delete=models.CASCADE, related_name="speaker_talks"
    )
    duration = models.IntegerField()
    category = models.CharField(max_length=100, choices=TalkCategoryChoices.choices)
    presentation_files = models.FileField(
        upload_to=PRESENTATION_FILES_UPLOAD_DIR, null=True
    )

    slug = models.SlugField(unique=True, max_length=255, null=True, blank=True)
    is_public = models.BooleanField(default=False)
    is_reviewable = models.BooleanField(default=True)

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="talk_event"
    )

    def __str__(self):
        """Str."""
        return self.title

    def _generate_unique_slug(self) -> str:
        """Generate a unique slug, appending random string for entropy."""
        base_slug = slugify(self.title) if self.title else "talk"
        random_suffix = get_random_string(length=5).lower()
        candidate = f"{base_slug}-{random_suffix}"

        # In the extremely rare case of a collision, try again
        while Talks.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
            random_suffix = get_random_string(length=5).lower()
            candidate = f"{base_slug}-{random_suffix}"

        return candidate

    def save(self, *args, **kwargs):
        """Set slug once when empty."""
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)


class TalkReviewComment(TimeStampedModel):
    """Talk review comment model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    talk = models.ForeignKey(
        "talks.Talks",
        on_delete=models.CASCADE,
        related_name="talk_review_comments",
        db_index=True,
        null=True,
    )
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5.",
    )
    comment = models.TextField(help_text="Comment on talk.")

    def __str__(self):
        """Str."""
        return f"{self.talk.title} - {self.comment[:50]}..."

    class Meta:
        """meta options."""

        verbose_name = "Talk Review Comment"
        verbose_name_plural = "Talk Review Comments"
