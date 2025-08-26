"""s model."""

from django.contrib.auth import get_user_model
from django.db import models

from base.models import SocialLinks, TimeStampedModel

# from events.models import Event


class AttendeeProfile(TimeStampedModel):
    """s model."""

    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    email = models.EmailField(unique=True)
    notification_preference = models.CharField(max_length=255, null=True)
    organization = models.CharField(max_length=255, null=True)
    is_verified = models.BooleanField(default=False)
    user_account = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="attendee_profile_user",
    )

    def __str__(self):
        """Str method."""
        return f"{self.first_name} {self.last_name}"

    def events_attended(self):
        """Return the number of events attended by the attendee."""
        # TODO: events_attended = Events.objects.filter(attendees__attendee=self)


class AttendeeSocialLinks(SocialLinks):
    """social links model."""

    attendee = models.ForeignKey(
        AttendeeProfile, on_delete=models.CASCADE, related_name="social_links"
    )

    def __str__(self):
        """Str method."""
        return self.name


class Attendance(TimeStampedModel):
    """Attendance model."""

    attendee = models.ForeignKey(
        AttendeeProfile, on_delete=models.CASCADE, related_name="attendances", null=True
    )
    event = models.ForeignKey(
        "events.Event", on_delete=models.CASCADE, related_name="attendees"
    )
    check_in_time = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(null=True)
    username = models.CharField(max_length=255, null=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        """Meta class."""

        unique_together = ("attendee", "event")

    def __str__(self):
        """Str method."""
        return f"{self.attendee} attended {self.event}"

    def mark_as_verified(self):
        """Mark the attendance as verified."""
        self.is_verified = True
        self.save()
        return True
