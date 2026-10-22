"""Devfolio adapter backed by the hackathon's embedded Next.js payload."""

from __future__ import annotations

import typing
from typing import Any
from urllib.parse import urlsplit

from events.services.event_import.extract.base import (
    Extraction,
    ExtractionContext,
    ImageCandidate,
    next_data,
)
from events.services.event_import.normalizers import compose_location, markdown_to_text

if typing.TYPE_CHECKING:
    pass

SOURCE = "platform:devfolio"


class DevfolioAdapter:
    """Extract a hackathon from Devfolio's pageProps.hackathon payload."""

    platform = "devfolio"

    def supports(self, url: str) -> bool:
        """Return whether the URL belongs to Devfolio or a hackathon subdomain."""
        hostname = (urlsplit(url).hostname or "").lower()
        return hostname == "devfolio.co" or hostname.endswith(".devfolio.co")

    def extract(self, context: ExtractionContext) -> Extraction:
        """Return canonical fields."""
        page_props = next_data(context.soup).get("props", {}).get("pageProps", {})
        hackathon = page_props.get("hackathon")
        if not isinstance(hackathon, dict):
            return Extraction(source=SOURCE)

        fields: dict[str, Any] = {}
        title = _text(hackathon.get("name"))
        if title:
            fields["title"] = title

        description = markdown_to_text(_text(hackathon.get("desc")))
        if description:
            fields["description"] = description

        start = _text(hackathon.get("starts_at"))
        if start:
            fields["start_date_time"] = start
        end = _text(hackathon.get("ends_at"))
        if end:
            fields["end_date_time"] = end

        location = compose_location(
            _text(hackathon.get("location")) or _text(hackathon.get("city")),
            None,
        )
        if location:
            fields["location"] = location
        country = _text(hackathon.get("country"))
        if country:
            fields["country"] = country

        is_free = _devfolio_is_free(hackathon)
        if is_free is not None:
            fields["is_free"] = is_free

        image = _text(hackathon.get("cover_img"))
        if image:
            fields["event_image_candidates"] = [
                ImageCandidate(url=image, source=SOURCE)
            ]

        settings = hackathon.get("settings")
        if isinstance(settings, dict):
            website = _text(settings.get("site"))
            if website:
                fields["website"] = website

        return Extraction(source=SOURCE, fields=fields)


def _devfolio_is_free(hackathon: dict) -> bool | None:
    """Return the inverse of Devfolio's paid-registration flag."""
    settings = hackathon.get("settings")
    if not isinstance(settings, dict):
        return None
    paid = settings.get("paid")
    if isinstance(paid, bool):
        return not paid
    return None


def _text(value: object) -> str | None:
    """Return a trimmed string for scalar values."""
    if isinstance(value, str):
        text = value.strip()
        return text or None
    return None
