"""speaker request app config."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SpeakerrequestsConfig(AppConfig):
    """speaker request app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "speakerrequests"
    verbose_name = _("RequestSpeaker")
