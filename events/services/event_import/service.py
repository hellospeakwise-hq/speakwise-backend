"""Orchestration for building an event import preview from a public URL."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup
from django.utils import timezone

from events.models import Event
from events.services.event_import.extract import EXTRACTORS
from events.services.event_import.extract.base import (
    ExtractionContext,
    ImageCandidate,
    warning,
)
from events.services.event_import.extract.platform import detect_platform
from events.services.event_import.fetcher import fetch_html
from events.services.event_import.images import select_image_candidate, sign_image_token
from events.services.event_import.normalizers import (
    absolute_url,
    normalize_country,
    parse_datetime_value,
    strip_html,
    strip_tracking_params,
    truncate,
)
from events.services.event_import.schemas import (
    CANONICAL_IMPORT_FIELDS,
    DESCRIPTION_MAX_LENGTH,
    LOCATION_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    EventImportDraft,
    EventImportPreview,
)


def build_event_import_preview(url: str, user_id: object) -> EventImportPreview:
    """Fetch an event page and return a normalised draft for user review.

    The page is fetched once, parsed once, and passed through every extractor
    in precision order. Nothing is persisted; the caller receives a draft, the
    source of each field, any warnings, and a signed image token.
    """
    document = fetch_html(url)
    soup = BeautifulSoup(document.content, "html.parser")
    context = ExtractionContext(url=document.url, soup=soup)

    values, image_candidates, warnings = _merge_extractions(context)
    draft = _build_draft(values, document.url, warnings)

    image_token = None
    candidate = select_image_candidate(image_candidates)
    if candidate is not None:
        draft.event_image_url = candidate.url
        # field_sources["event_image_url"] = candidate.source
        image_token = sign_image_token(candidate.url, user_id)

    _add_context_warnings(draft, warnings)
    missing_fields = [
        field
        for field in CANONICAL_IMPORT_FIELDS
        if not _has_value(getattr(draft, field))
    ]
    if not any(
        field in values
        for field in ("title", "description", "start_date_time", "location")
    ):
        _append_warning(
            warnings,
            "no_event_data",
            "No event details could be found on this page; enter them manually.",
        )

    return EventImportPreview(
        source_url=document.url,
        platform=detect_platform(document.url),
        fetched_at=timezone.now(),
        draft=draft,
        # field_sources=field_sources,
        missing_fields=missing_fields,
        warnings=warnings,
        event_image_token=image_token,
    )


def _merge_extractions(
    context: ExtractionContext,
) -> tuple[dict[str, Any], list[ImageCandidate], list[dict[str, str]], dict[str, str]]:
    """Run every extractor and fill each canonical field from the best source."""
    values: dict[str, Any] = {}
    # field_sources: dict[str, str] = {}
    warnings: list[dict[str, str]] = []
    image_candidates: list[ImageCandidate] = []

    for extractor in EXTRACTORS:
        extraction = extractor(context)
        warnings.extend(extraction.warnings)
        for field, value in extraction.fields.items():
            if field == "event_image_candidates":
                image_candidates.extend(value)
            elif (
                field in CANONICAL_IMPORT_FIELDS
                and not _has_value(values.get(field))
                and _has_value(value)
            ):
                values[field] = value
                # field_sources[field] = extraction.source

    return values, image_candidates, warnings


def _build_draft(
    values: dict[str, Any], page_url: str, warnings: list[dict[str, str]]
) -> EventImportDraft:
    """Normalise merged values into the Event-shaped draft."""
    draft = EventImportDraft()

    title, truncated = truncate(
        strip_html(_as_str(values.get("title"))), TITLE_MAX_LENGTH
    )
    if truncated:
        _append_warning(warnings, "title_truncated", "The event title was truncated.")
    draft.title = title

    description, truncated = truncate(
        strip_html(_as_str(values.get("description"))), DESCRIPTION_MAX_LENGTH
    )
    if truncated:
        _append_warning(
            warnings, "description_truncated", "The event description was truncated."
        )
    draft.description = description

    draft.start_date_time = _draft_datetime(
        values.get("start_date_time"), warnings, "start_date_time"
    )
    draft.end_date_time = _draft_datetime(
        values.get("end_date_time"), warnings, "end_date_time"
    )
    if (
        draft.start_date_time
        and draft.end_date_time
        and _comparable(draft.end_date_time) < _comparable(draft.start_date_time)
    ):
        _append_warning(
            warnings, "end_before_start", "The end date is earlier than the start date."
        )

    location, truncated = truncate(
        strip_html(_as_str(values.get("location"))), LOCATION_MAX_LENGTH
    )
    if truncated:
        _append_warning(warnings, "location_truncated", "The location was truncated.")
    draft.location = location
    draft.country = normalize_country(_as_str(values.get("country")))

    is_free = values.get("is_free")
    draft.is_free = is_free if isinstance(is_free, bool) else None

    website = absolute_url(page_url, _as_str(values.get("website"))) or page_url
    draft.website = strip_tracking_params(website)

    return draft


def _draft_datetime(
    value: object, warnings: list[dict[str, str]], field: str
) -> datetime | None:
    """Parse one structured date and record the reason when it is missing."""
    parsed, code = parse_datetime_value(value)
    if code == "date_only":
        _append_warning(
            warnings,
            "date_only",
            f"The {field.replace('_', ' ')} had no time; midnight was assumed.",
        )
    elif code == "invalid_date":
        _append_warning(
            warnings,
            "invalid_date",
            f"The {field.replace('_', ' ')} could not be read.",
        )
    return parsed


def _add_context_warnings(
    draft: EventImportDraft, warnings: list[dict[str, str]]
) -> None:
    """Add duplicate and past-event warnings based on existing data."""
    if draft.title:
        duplicate = Event.objects.find_duplicate(
            title=draft.title, website=draft.website or ""
        )
        if duplicate is not None:
            _append_warning(
                warnings,
                "duplicate_event",
                f"An event with this name and website already exists ({duplicate.slug}).",
            )
        elif Event.objects.filter(title__iexact=draft.title).exists():
            _append_warning(
                warnings,
                "duplicate_title",
                "Another event already uses this title.",
            )

    end = draft.end_date_time or draft.start_date_time
    if end is not None and _comparable(end) < timezone.now():
        _append_warning(
            warnings,
            "event_in_past",
            "This event appears to have already ended.",
        )


def _comparable(value: datetime) -> datetime:
    """Return an aware datetime so naive and aware values can be compared."""
    return timezone.make_aware(value) if timezone.is_naive(value) else value


def _as_str(value: object) -> str | None:
    """Return a trimmed string for scalar extractor values."""
    if isinstance(value, str):
        return value.strip() or None
    return None


def _has_value(value: object) -> bool:
    """Return whether an extracted value should count as present."""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, bool):
        return True
    return bool(value)


def _append_warning(warnings: list[dict[str, str]], code: str, message: str) -> None:
    """Append a warning unless one with the same code is already present."""
    if not any(item.get("code") == code for item in warnings):
        warnings.append(warning(code, message))
