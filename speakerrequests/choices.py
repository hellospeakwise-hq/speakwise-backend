"""speaker request model choices."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class SpeakerRequestStatus(models.TextChoices):
    """speaker request saturation choices."""

    ACCEPTED = "accepted", _("Accepted")
    DECLINED = "declined", _("Declined")
    PENDING = "pending", _("Pending")
