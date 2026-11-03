"""Application configuration for badges app."""

from django.apps import AppConfig


class BadgesConfig(AppConfig):
    """Configuration for SpeakWise badges and gamification app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "badges"

    def ready(self):
        """Register signal receivers when app is ready."""
        import badges.signals  # noqa: F401
