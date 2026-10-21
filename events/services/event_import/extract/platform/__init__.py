"""Hostname-keyed platform adapters for sites without schema.org data."""

from __future__ import annotations

from urllib.parse import urlsplit

from events.services.event_import.extract.base import Extraction, ExtractionContext
from events.services.event_import.extract.platform.devfolio import DevfolioAdapter
from events.services.event_import.extract.platform.luma import LumaAdapter

ADAPTERS = (LumaAdapter(), DevfolioAdapter())

# Platforms that publish schema.org JSON-LD and therefore need no adapter,
# but are still labelled in the preview response.
PLATFORM_HOST_SUFFIXES = (
    ("eventbrite", ("eventbrite.com",)),
    ("meetup", ("meetup.com",)),
    ("konfhub", ("konfhub.com", "konfhub.me")),
)


def extract_platform(context: ExtractionContext) -> Extraction:
    """Return fields from the first adapter that supports the URL."""
    for adapter in ADAPTERS:
        if adapter.supports(context.url):
            return adapter.extract(context)
    return Extraction(source="platform")


def detect_platform(url: str) -> str:
    """Return a short platform label for the preview response."""
    hostname = (urlsplit(url).hostname or "").lower()
    for adapter in ADAPTERS:
        if adapter.supports(url):
            return adapter.platform
    for name, suffixes in PLATFORM_HOST_SUFFIXES:
        if any(
            hostname == suffix or hostname.endswith("." + suffix) for suffix in suffixes
        ):
            return name
    return "generic"
