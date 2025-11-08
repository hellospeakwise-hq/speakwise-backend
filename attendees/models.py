"""s model."""

from django.contrib.auth import get_user_model
from django.db import models

from base.models import SocialLinks, TimeStampedModel

# from events.models import Event


class AttendeeProfile(TimeStampedModel):
    """s model."""

    user_account = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="attendee_profile_user",
    )
    notification_preference = models.CharField(max_length=255, null=True)
    organization = models.CharField(max_length=255, null=True)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        """Str method."""
        return f"{self.user_account.first_name} {self.user_account.last_name}"

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

    event = models.ForeignKey(
        "events.Event", on_delete=models.CASCADE, related_name="event_attendance"
    )
    check_in_time = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(null=True)
    username = models.CharField(max_length=255, null=True)
    is_verified = models.BooleanField(default=False)
    is_given_feedback = models.BooleanField(default=False)

    def __str__(self):
        """Str method."""
        return f"{self.email} attended {self.event}"

    def mark_as_verified(self):
        """Mark the attendance as verified."""
        self.is_verified = True
        self.save()
        return True

    def is_user(self):
        """Check if the user is the attendee."""
        return get_user_model().objects.filter(email=self.email).exists()

    def mark_as_given_feedback(self):
        """Mark the attendance as given feedback."""
        self.is_given_feedback = True
        self.save()
        return True
