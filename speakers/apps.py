"""speakers app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SpeakersConfig(AppConfig):
    """speakers app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "speakers"
    verbose_name = _("Speakers")
