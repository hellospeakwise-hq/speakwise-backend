"""Organization model for user profiles."""

import uuid

from django.db import models
from django.utils import timezone

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
    cfps = models.ForeignKey(
        "profiles.OrganizationCFP",
        on_delete=models.SET_NULL,
        null=True,
        related_name="organization_cfp",
    )

    def __str__(self):
        """String representation of the organization profile."""
        return self.name

    def get_open_cfps(self):
        """Return all open CFPs for the organization."""
        return self.cfp.filter(
            open_at__lte=timezone.now(), close_at__gte=timezone.now()
        )

    def get_closed_cfps(self):
        """Return all closed CFPs for the organization."""
        return self.cfp.filter(close_at__lt=timezone.now())


class OrganizationCFP(TimeStampedModel):
    """Organization CFP model."""

    url = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    open_at = models.DateTimeField(blank=True, null=True)
    close_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        """String representation of the organization CFP."""
        return self.url
