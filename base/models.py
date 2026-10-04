"""base models."""

from django.db import models


class TimeStampedModel(models.Model):
    """time stamped model."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """meta options."""

        abstract = True


class SocialLinks(TimeStampedModel):
    """social links model."""

    name = models.CharField(null=True, max_length=255)
    link = models.URLField(null=True, max_length=255)

    class Meta:
        """meta options."""

        abstract = True
