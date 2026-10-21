"""OpenGraph, Twitter card, and meta tag extraction."""

from __future__ import annotations

from typing import Any

from events.services.event_import.extract.base import (
    Extraction,
    ExtractionContext,
    ImageCandidate,
)

SOURCE = "open_graph"


def extract(context: ExtractionContext) -> Extraction:
    """Return Event fields from OpenGraph, Twitter, and standard meta tags."""
    soup = context.soup
    fields: dict[str, Any] = {}

    title = _meta_first(soup, "og:title", "twitter:title")
    if title:
        fields["title"] = title

    description = _meta_first(
        soup, "og:description", "twitter:description", "description"
    )
    if description:
        fields["description"] = description

    website = _meta_first(soup, "og:url") or _canonical_url(soup)
    if website:
        fields["website"] = website

    start_date = _meta_first(soup, "event:start_time")
    if start_date:
        fields["start_date_time"] = start_date
    end_date = _meta_first(soup, "event:end_time")
    if end_date:
        fields["end_date_time"] = end_date

    location = _meta_first(soup, "event:location")
    if location:
        fields["location"] = location

    candidates = _image_candidates(soup)
    if candidates:
        fields["event_image_candidates"] = candidates

    return Extraction(source=SOURCE, fields=fields)


def _meta_first(soup, *keys: str) -> str | None:
    """Return the first non-empty meta content matching the given keys."""
    for key in keys:
        for attribute in ("property", "name", "itemprop"):
            tag = soup.find("meta", attrs={attribute: key})
            if tag and tag.get("content"):
                content = tag["content"].strip()
                if content:
                    return content
    return None


def _meta_all(soup, key: str) -> list[str]:
    """Return every meta content value for a repeated property such as og:image.

    Platforms sometimes emit the same key as a ``property`` and sometimes as a
    ``name`` (Twitter cards commonly use ``name``), so both are checked.
    """
    values = []
    for tag in soup.find_all("meta"):
        if tag.get("property") != key and tag.get("name") != key:
            continue
        content = (tag.get("content") or "").strip()
        if content:
            values.append(content)
    return values


def _canonical_url(soup) -> str | None:
    """Return the link rel=canonical href when present."""
    tag = soup.find("link", attrs={"rel": "canonical"})
    if tag and tag.get("href"):
        return str(tag["href"]).strip() or None
    return None


def _image_candidates(soup) -> list[ImageCandidate]:
    """Return OpenGraph and Twitter image candidates with their dimensions."""
    candidates: list[ImageCandidate] = []
    widths = _meta_all(soup, "og:image:width")
    heights = _meta_all(soup, "og:image:height")

    for index, url in enumerate(_meta_all(soup, "og:image")):
        candidates.append(
            ImageCandidate(
                url=url,
                source=SOURCE,
                width=_int_or_none(widths[index]) if index < len(widths) else None,
                height=_int_or_none(heights[index]) if index < len(heights) else None,
            )
        )
    for url in _meta_all(soup, "og:image:secure_url"):
        candidates.append(ImageCandidate(url=url, source=SOURCE))
    for url in _meta_all(soup, "twitter:image"):
        candidates.append(ImageCandidate(url=url, source=SOURCE))

    return candidates


def _int_or_none(value: object) -> int | None:
    """Return an integer dimension or None for non-numeric values."""
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None
