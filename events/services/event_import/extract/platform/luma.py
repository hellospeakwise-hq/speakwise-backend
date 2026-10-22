"""Luma adapter backed by the page's embedded Next.js payload."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlsplit

from events.services.event_import.extract.base import (
    Extraction,
    ExtractionContext,
    ImageCandidate,
    next_data,
)
from events.services.event_import.extract.platform import text
from events.services.event_import.normalizers import (
    compose_location,
    rich_text_to_plain_text,
)

SOURCE = "platform:luma"
HOSTS = frozenset({"lu.ma", "luma.com", "www.lu.ma", "www.luma.com"})


class LumaAdapter:
    """Extract an event from Luma's __NEXT_DATA__ event payload."""

    platform = "luma"

    def supports(self, url: str) -> bool:
        """Return whether the URL belongs to a Luma host."""
        return (urlsplit(url).hostname or "").lower() in HOSTS

    def extract(self, context: ExtractionContext) -> Extraction:
        """Return canonical fields from props.pageProps.initialData.data."""
        page_props = next_data(context.soup).get("props", {}).get("pageProps", {})
        initial = page_props.get("initialData")
        if not isinstance(initial, dict):
            return Extraction(source=SOURCE)
        data = initial.get("data")
        if not isinstance(data, dict):
            return Extraction(source=SOURCE)

        event = data.get("event") if isinstance(data.get("event"), dict) else {}
        calendar = (
            data.get("calendar") if isinstance(data.get("calendar"), dict) else {}
        )
        fields: dict[str, Any] = {}

        title = text(event.get("name")) or text(data.get("name"))
        if title:
            fields["title"] = title

        description = rich_text_to_plain_text(data.get("description_mirror"))
        if description:
            fields["description"] = description

        start = text(event.get("start_at")) or text(data.get("start_at"))
        if start:
            fields["start_date_time"] = start
        end = text(event.get("end_at"))
        if end:
            fields["end_date_time"] = end

        location, country = _location_fields(event)
        if location:
            fields["location"] = location
        if country:
            fields["country"] = country

        is_free = _luma_is_free(data)
        if is_free is not None:
            fields["is_free"] = is_free

        candidates = _image_candidates(event, calendar, data)
        if candidates:
            fields["event_image_candidates"] = candidates

        website = text(calendar.get("website"))
        if website:
            fields["website"] = website

        return Extraction(source=SOURCE, fields=fields)


def _location_fields(event: dict) -> tuple[str | None, str | None]:
    """Return (location, country) from Luma's geo address payload."""
    if text(event.get("location_type")) == "online":
        return "Online", None

    geo = event.get("geo_address_info")
    if not isinstance(geo, dict):
        return None, None
    venue = text(geo.get("address")) or text(geo.get("full_address"))
    city = text(geo.get("city"))
    return compose_location(venue, city), text(geo.get("country"))


def _luma_is_free(data: dict) -> bool | None:
    """Return the ticket price classification Luma reports."""
    ticket_info = data.get("ticket_info")
    if not isinstance(ticket_info, dict):
        return None
    is_free = ticket_info.get("is_free")
    return is_free if isinstance(is_free, bool) else None


def _image_candidates(event: dict, calendar: dict, data: dict) -> list[ImageCandidate]:
    """Return Luma cover and social image candidates in display order."""
    candidates: list[ImageCandidate] = []
    urls = [
        text(event.get("cover_url")),
        text(event.get("social_image_url")),
        text(calendar.get("cover_image_url")),
    ]
    social_image = data.get("social_image")
    if isinstance(social_image, dict):
        urls.append(text(social_image.get("cdn_url")))

    for url in urls:
        if url:
            candidates.append(ImageCandidate(url=url, source=SOURCE))
    return candidates
