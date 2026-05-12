"""Events schedules models."""
import uuid

from django.db import models
from base.models import TimeStampedModel


class EventSchedule(TimeStampedModel):
    """Event schedule model."""
    
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    event = models.ForeignKey("events.Event", on_delete=models.CASCADE, 
                              related_name="event_schedules", null=False)
    