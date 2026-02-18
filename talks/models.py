"""talks models."""

from django.db import models

from base.models import TimeStampedModel
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

    event = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    is_public = models.BooleanField(
        default=False,
        help_text="When True, the talk proposal is visible for review by others",
    )

    def __str__(self):
        """Str."""
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            from django.utils.text import slugify

            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Talks.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)
