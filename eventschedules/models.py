"""Events schedules models."""

import uuid

from django.db import models

from base.models import TimeStampedModel


class EventSchedule(TimeStampedModel):
    """Event schedule model."""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    event = models.ForeignKey(
        "events.Event", on_delete=models.CASCADE, related_name="event_schedules"
    )
    sessions = models.ManyToManyField(
        "eventsessions.Session", related_name="event_schedules"
    )

    class Meta:
        """Events schedules model meta."""

        db_table = "event_schedules"
        indexes = [
            models.Index(fields=["event", "id"]),
        ]
        verbose_name = "Event Schedule"
        verbose_name_plural = "Event Schedules"
        ordering = ("-created_at",)

    def __str__(self):
        """Events schedule str."""
        return f"{self.event.title} Schedule"
