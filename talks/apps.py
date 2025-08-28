"""talks app configuration."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TalksConfig(AppConfig):
    """Configuration for talks app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "talks"
    verbose_name = _("Talks")
