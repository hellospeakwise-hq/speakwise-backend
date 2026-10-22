"""schema.org Event extraction from JSON-LD blocks."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any, Iterator

from django.utils import timezone

from events.services.event_import.extract.base import (
    Extraction,
    ExtractionContext,
    ImageCandidate,
    warning,
)
from events.services.event_import.normalizers import (
    absolute_url,
    compose_location,
    normalize_country,
    parse_datetime_value,
)
from events.utils import normalize_event_website

logger = logging.getLogger(__name__)

SOURCE = "json_ld"
EVENT_TYPE_SUFFIXES = ("event", "festival")


def extract(context: ExtractionContext) -> Extraction:
    """Return Event fields from every schema.org Event JSON-LD node found."""
    nodes = list(_iter_json_ld_nodes(context.soup))
    events = [node for node in nodes if _is_event_node(node)]
    if not events:
        return Extraction(source=SOURCE)

    node, selection_warning = _choose_event(events, context.url)
    warnings = [selection_warning] if selection_warning else []
    fields: dict[str, Any] = {}

    title = _text(node.get("name"))
    if title:
        fields["title"] = title

    description = _text(node.get("description"))
    if description:
        fields["description"] = description

    start_date = _text(node.get("startDate"))
    if start_date:
        fields["start_date_time"] = start_date
    end_date = _text(node.get("endDate"))
    if end_date:
        fields["end_date_time"] = end_date

    location, country = _location_fields(node.get("location"))
    attendance_mode = (_text(node.get("eventAttendanceMode")) or "").lower()
    if "online" in attendance_mode and not location:
        location = "Online"
    if location:
        fields["location"] = location
    if country:
        fields["country"] = country

    is_free = _offers_is_free(node.get("offers"))
    if is_free is not None:
        fields["is_free"] = is_free

    candidates = _image_candidates(node.get("image"))
    if candidates:
        fields["event_image_candidates"] = candidates

    event_url = _event_url(node)
    if event_url:
        fields["website"] = event_url

    if "cancelled" in (_text(node.get("eventStatus")) or "").lower():
        warnings.append(
            warning(
                "event_cancelled",
                "The event page says this event was cancelled.",
            )
        )

    return Extraction(source=SOURCE, fields=fields, warnings=warnings)


def _iter_json_ld_nodes(soup) -> Iterator[dict]:
    """Yield every JSON-LD object, flattening lists and @graph containers."""
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = (script.string or script.get_text() or "").strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Malformed markup is common; other extractors still run.
            logger.debug("Skipping malformed JSON-LD block")
            continue
        yield from _flatten(data)


def _flatten(data: object) -> Iterator[dict]:
    """Flatten nested lists and @graph entries into individual nodes."""
    if isinstance(data, list):
        for item in data:
            yield from _flatten(item)
    elif isinstance(data, dict):
        yield data
        graph = data.get("@graph")
        if isinstance(graph, (list, dict)):
            yield from _flatten(graph)


def _is_event_node(node: dict) -> bool:
    """Return whether a JSON-LD node types to Event or an Event subtype."""
    raw_types = node.get("@type")
    types = raw_types if isinstance(raw_types, list) else [raw_types]
    for raw_type in types:
        if not isinstance(raw_type, str):
            continue
        short = raw_type.rsplit("/", 1)[-1].rsplit(":", 1)[-1].lower()
        if short.endswith(EVENT_TYPE_SUFFIXES):
            return True
    return False


def _choose_event(events: list[dict], page_url: str) -> tuple[dict, dict | None]:
    """Pick the Event node matching the page, or the next upcoming one."""
    if len(events) == 1:
        return events[0], None

    target = normalize_event_website(page_url)
    for node in events:
        candidate = absolute_url(page_url, _event_url(node))
        if candidate and normalize_event_website(candidate) == target:
            return node, _multiple_events_warning()

    now = timezone.now()
    dated: list[tuple[datetime, dict]] = []
    for node in events:
        start, _ = parse_datetime_value(node.get("startDate"))
        if start is None:
            continue
        if timezone.is_naive(start):
            start = timezone.make_aware(start)
        dated.append((start, node))

    upcoming = [(start, node) for start, node in dated if start >= now]
    if upcoming:
        return min(upcoming, key=lambda item: item[0])[1], _multiple_events_warning()
    return events[0], _multiple_events_warning()


def _multiple_events_warning() -> dict[str, str]:
    """Warn that the page listed several events and one was selected."""
    return warning(
        "multiple_events",
        "The page lists several events; the closest one was selected.",
    )


def _text(value: object) -> str | None:
    """Return a trimmed string from a JSON-LD value."""
    if isinstance(value, str):
        text = value.strip()
        return text or None
    if isinstance(value, list):
        for item in value:
            text = _text(item)
            if text:
                return text
    if isinstance(value, dict):
        for key in ("name", "url", "@id"):
            text = _text(value.get(key))
            if text:
                return text
    return None


def _event_url(node: dict) -> str | None:
    """Return the node's own URL without falling back to nested values."""
    for key in ("url", "@id"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _image_candidates(value: object) -> list[ImageCandidate]:
    """Flatten the schema.org image values into candidate images."""
    candidates: list[ImageCandidate] = []

    def _add(item: object) -> None:
        if isinstance(item, str):
            if item.strip():
                candidates.append(ImageCandidate(url=item.strip(), source=SOURCE))
        elif isinstance(item, list):
            for child in item:
                _add(child)
        elif isinstance(item, dict):
            url = item.get("contentUrl") or item.get("url") or item.get("@id")
            if isinstance(url, str) and url.strip():
                candidates.append(
                    ImageCandidate(
                        url=url.strip(),
                        source=SOURCE,
                        width=_int_or_none(item.get("width")),
                        height=_int_or_none(item.get("height")),
                    )
                )

    _add(value)
    return candidates


def _location_fields(value: object) -> tuple[str | None, str | None]:
    """Return (location, country) from a schema.org location value."""
    if isinstance(value, list):
        for item in value:
            location, country = _location_fields(item)
            if location or country:
                return location, country
        return None, None
    if isinstance(value, str):
        return value.strip() or None, None
    if not isinstance(value, dict):
        return None, None

    node_type = (_text(value.get("@type")) or "").lower()
    if "virtuallocation" in node_type:
        return "Online", None

    venue = _text(value.get("name"))
    address = value.get("address")
    if isinstance(address, list):
        address = next((item for item in address if isinstance(item, dict)), None)
    city = None
    country = None
    if isinstance(address, dict):
        city = _text(address.get("addressLocality")) or _text(
            address.get("addressRegion")
        )
        country = _text(address.get("addressCountry"))
    if venue and city and venue.lower() == city.lower():
        venue = None
    return compose_location(venue, city), normalize_country(country)


def _offers_is_free(value: object) -> bool | None:
    """Return whether any structured offer is free, or None when unknown."""
    offers = value if isinstance(value, list) else [value]
    verdicts: list[bool] = []
    for offer in offers:
        if not isinstance(offer, dict):
            continue
        accessible = offer.get("isAccessibleForFree")
        if isinstance(accessible, bool):
            verdicts.append(accessible)
        elif isinstance(accessible, str) and accessible.lower() in {"true", "false"}:
            verdicts.append(accessible.lower() == "true")
        price = offer.get("price")
        if price is None:
            price = offer.get("lowPrice")
        if price is not None:
            try:
                verdicts.append(float(str(price).replace(",", "")) == 0)
            except ValueError:
                continue
    if not verdicts:
        return None
    return any(verdicts)


def _int_or_none(value: object) -> int | None:
    """Return an integer dimension or None for non-numeric values."""
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
