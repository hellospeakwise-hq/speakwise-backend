"""Shared constants used across the SpeakWise codebase."""

from django.conf import settings

FRONTEND_URL = getattr(settings, "FRONTEND_URL", "https://speak-wise.live")
SITE_NAME = getattr(settings, "SITE_NAME", "SpeakWise")
