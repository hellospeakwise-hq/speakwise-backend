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
        return self.talk


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

    # TODO: event = models.ForeignKey(
    #     "events.Event", on_delete=models.CASCADE, related_name="talk_event"
    # )

    def __str__(self):
        """Str."""
        return self.title
