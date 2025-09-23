"""s model."""

from django.contrib.auth import get_user_model
from django.db import models

from base.models import SocialLinks, TimeStampedModel


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


class AttendeeSocialLinks(SocialLinks):
    """social links model."""

    attendee = models.ForeignKey(
        AttendeeProfile, on_delete=models.CASCADE, related_name="social_links"
    )

    def __str__(self):
        """Str method."""
        return self.name
