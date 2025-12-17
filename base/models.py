"""base models."""

from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    """time stamped model."""

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        """meta options."""

        abstract = True


class SocialLinks(TimeStampedModel):
    """social links model."""

    name = models.CharField(null=True, max_length=255, unique=True)
    link = models.URLField(null=True, max_length=255, unique=True)

    class Meta:
        """meta options."""

        abstract = True
