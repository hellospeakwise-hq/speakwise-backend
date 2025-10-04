"""speaker request model."""

from django.db import models

from base.models import TimeStampedModel
from organizers.models import OrganizerProfile
from speakerrequests.choices import RequestStatusChoices
from speakers.models import SpeakerProfile


class SpeakerRequest(TimeStampedModel):
    """speaker request model."""

    organizer = models.ForeignKey(OrganizerProfile, on_delete=models.DO_NOTHING)
    speaker = models.ForeignKey(SpeakerProfile, on_delete=models.DO_NOTHING)
    event = models.ForeignKey("events.Event", on_delete=models.DO_NOTHING)
    status = models.CharField(
        max_length=10,
        choices=RequestStatusChoices.choices,
        default=RequestStatusChoices.PENDING,
    )
    message = models.TextField(null=False)

    def __str__(self):
        """Str."""
        return f"{self.speaker.user_account.username} request"
