"""Event schedules app config."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class EventschedulesConfig(AppConfig):
    """Event schedules app config."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "eventschedules"
    verbose_name = _("Event Schedules")
