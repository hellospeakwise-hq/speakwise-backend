"""attendees model."""

from django.db import models
from django.contrib.auth import get_user_model


class Attendee(models.Model):
    """attendees model."""

    first_name = models.CharField(max_length=255, null=True)
    last_name = models.CharField(max_length=255, null=True)
    email = models.EmailField(unique=True)
    notification_preference = models.CharField(max_length=255, null=True)
    organization = models.CharField(max_length=255, null=True)
    is_verified = models.BooleanField(default=False)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="attendee",
        null=True,
    )

    def __str__(self):
        """Str method."""
        return f"{self.first_name} {self.last_name}"


class AttendeeSocialLinks(models.Model):
    """attendee social links model."""

    attendee = models.ForeignKey(
        Attendee, on_delete=models.CASCADE, related_name="social_links"
    )
