"""Organization model for user profiles."""

import uuid

from django.db import models

from base.models import TimeStampedModel


class OrganizationProfile(TimeStampedModel):
    """Organization profile model."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, help_text="Organization name")
    description = models.TextField(
        blank=True, null=True, help_text="A brief description of the organization"
    )
    website = models.URLField(
        blank=True, null=True, help_text="Organization website URL"
    )
    branding = models.ImageField(
        upload_to="organization_branding/",
        blank=True,
        null=True,
        help_text="Organization branding image",
    )
    contact_email = models.EmailField(
        blank=True, null=True, help_text="Contact email for the organization"
    )
    website = models.URLField(
        blank=True, null=True, help_text="Organization website URL"
    )

    def __str__(self):
        """String representation of the organization profile."""
        return self.name
