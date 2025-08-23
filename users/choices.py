"""user role choices."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class UserRoleChoices(models.TextChoices):
    """user role choices."""

    ATTENDEE = "attendee", _("Attendee")
    ORGANIZATION = "organizer", _("Organizer")
    SPEAKER = "speaker", _("Speaker")
    ADMIN = "admin", _("Admin")
