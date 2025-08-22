""" "talks models."""

from django.db import models
from base.models import TimeStampedModel
from talks.choices import TalkCategoryChoices
from speakers.models import SpeakerProfile


class Talks(TimeStampedModel):
    """Talks model."""

    title = models.CharField(max_length=255)
    description = models.TextField()
    speaker = models.ForeignKey(
        SpeakerProfile, on_delete=models.CASCADE, related_name="speaker_talks"
    )
    duration = models.IntegerField()
    category = models.CharField(max_length=100, choices=TalkCategoryChoices.choices)
    # TODO: event = models.ForeignKey(
    #     "events.Event", on_delete=models.CASCADE, related_name="talk_event"
    # )

    def __str__(self):
        return self.title
