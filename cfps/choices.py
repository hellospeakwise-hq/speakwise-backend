"""CFP choices."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TalkTypeChoices(models.TextChoices):
    """Talk type choices."""

    SHORT = "short", _("Short Talk")
    DEMO = "demo", _("Demo")
    LONG = "long", _("Long Talk")


class AudienceLevelChoices(models.TextChoices):
    """Audience level choices."""

    BEGINNER = "beginner", _("Beginner")
    INTERMEDIATE = "intermediate", _("Intermediate")
    ADVANCED = "advanced", _("Advanced")
    ALL = "all", _("All Levels")


class CFPStatusChoices(models.TextChoices):
    """CFP submission status choices."""

    PENDING = "pending", _("Pending")
    ACCEPTED = "accepted", _("Accepted")
    REJECTED = "rejected", _("Rejected")
