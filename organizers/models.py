"""Organizer models."""

from django.contrib.auth import get_user_model
from django.db import models

from base.models import SocialLinks, TimeStampedModel

# Organizers file upload directory
ORGANIZERS_UPLOAD_DIR = "organizers/avatars/"


class OrganizerProfile(TimeStampedModel):
    """Organizer model."""

    user_account = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name="organizer_user_profile",
    )
    # TODO: events = models.ManyToManyField(Event, blank=True, related_name="organizers")
    organization = models.CharField(max_length=255, blank=True)
    bio = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to=ORGANIZERS_UPLOAD_DIR, blank=True)

    class Meta:
        """Meta options for the Organizer model."""

        db_table = "organizers"
        verbose_name = "Organizer"
        verbose_name_plural = "Organizers"

    def __str__(self):
        """String representation of the Organizer."""
        return (
            self.organization
            or self.user_account.get_full_name()
            or self.user_account.email
        )


class OrganizerSocialLinks(SocialLinks):
    """Organizer social link model."""

    organizer = models.ForeignKey(
        OrganizerProfile, on_delete=models.CASCADE, related_name="social_links"
    )

    def __str__(self):
        """String representation of the Organizer Social Links."""
        return self.name
