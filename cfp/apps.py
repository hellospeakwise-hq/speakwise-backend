"""CFP app config."""

from django.apps import AppConfig


class CfpConfig(AppConfig):
    """App config for the CFP app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "cfp"
