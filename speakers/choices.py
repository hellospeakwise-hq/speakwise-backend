"""speaker choices."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class EventTypeChoices(models.TextChoices):
    """event type choices."""

    CONFERENCE = "conference", _("Conference")
    WORKSHOP = "workshop", _("Workshop")
    WEBINAR = "webinar", _("Webinar")
    MEETUP = "meetup", _("Meetup")
    COOPERATE_EVENT = "cooperate event", _("Cooperate event")
    OTHER = "other", _("Other")


