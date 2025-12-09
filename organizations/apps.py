"""Configuration for the organizations app."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrganizationsConfig(AppConfig):
    """Configuration for the organizations app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "organizations"
    verbose_name = _("Organizations")
