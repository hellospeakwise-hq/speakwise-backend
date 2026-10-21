"""Canonical shapes shared by event import extractors and the API response."""

from dataclasses import dataclass, field
from datetime import datetime

CANONICAL_IMPORT_FIELDS: tuple[str, ...] = (
    "title",
    "description",
    "website",
    "start_date_time",
    "end_date_time",
    "location",
    "country",
    "is_free",
    "event_image_url",
)

# Limits chosen to match the Event model fields where applicable.
TITLE_MAX_LENGTH = 255
LOCATION_MAX_LENGTH = 150
DESCRIPTION_MAX_LENGTH = 10_000


@dataclass
class EventImportDraft:
    """Normalised event data extracted from an external page.

    The attribute names match the Event model so the payload can be reviewed
    in the existing submission form without a translation layer.
    """

    title: str | None = None
    description: str | None = None
    website: str | None = None
    start_date_time: datetime | None = None
    end_date_time: datetime | None = None
    location: str | None = None
    country: str | None = None
    is_free: bool | None = None
    event_image_url: str | None = None


@dataclass
class EventImportPreview:
    """Everything the review form needs to prefill an event submission."""

    source_url: str
    platform: str
    fetched_at: datetime
    draft: EventImportDraft
    # field_sources: dict[str, str] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    warnings: list[dict[str, str]] = field(default_factory=list)
    event_image_token: str | None = None
