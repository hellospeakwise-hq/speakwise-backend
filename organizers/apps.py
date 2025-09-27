"""Configuration for the organizers app."""

import contextlib

from django.apps import AppConfig


class OrganizersConfig(AppConfig):
    """Configuration for the organizers app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "organizers"

    def ready(self):
        """Override the default ready function."""
        with contextlib.suppress(ImportError):
            import organizers.tasks  # noqa: F401
