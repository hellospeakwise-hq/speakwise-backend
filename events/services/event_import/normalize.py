"""Normalisation helpers for extracted event data."""

from __future__ import annotations

import re
from datetime import datetime, time
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import pycountry
from bs4 import BeautifulSoup
from dateutil.parser import isoparse
from django.utils.dateparse import parse_date, parse_datetime

_ZERO_WIDTH_CHARS = dict.fromkeys(map(ord, "\u200b\u200c\u200d\ufeff"), None)
_DATE_ONLY_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_WHITESPACE_PATTERN = re.compile(r"[ \t]+")
_BLANK_LINES_PATTERN = re.compile(r"\n\s*\n\s*\n+")

_TRACKING_PARAMS = frozenset(
    {
        "fbclid",
        "gclid",
        "igshid",
        "mc_cid",
        "mc_eid",
        "yclid",
    }
)


def strip_html(value: str | None) -> str | None:
    """Convert an HTML fragment to trimmed plain text.

    Page descriptions frequently contain markup, boilerplate line breaks, and
    zero-width characters; all of it is removed before the draft is returned.
    """
    if not value:
        return None
    text = BeautifulSoup(value, "html.parser").get_text("\n")
    text = text.translate(_ZERO_WIDTH_CHARS)
    text = _WHITESPACE_PATTERN.sub(" ", text)
    text = _BLANK_LINES_PATTERN.sub("\n\n", text)
    return text.strip() or None


def markdown_to_text(value: str | None) -> str | None:
    """Strip the most common markdown syntax before plain-text cleanup."""
    if not value:
        return None
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", value)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`{1,3}([^`]+)`{1,3}", r"\1", text)
    text = re.sub(r"^[ \t]{0,3}#{1,6}[ \t]*", "", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*|__|~~", "", text)
    return strip_html(text)


def truncate(value: str | None, max_length: int) -> tuple[str | None, bool]:
    """Return the value capped at max_length and whether it was truncated."""
    if not value:
        return None, False
    if len(value) <= max_length:
        return value, False
    return value[:max_length].rstrip(), True


def parse_datetime_value(value: object) -> tuple[datetime | None, str | None]:
    """Parse a structured date value into a datetime.

    Returns the datetime and an optional warning code: ``date_only`` when the
    source had no time component, ``invalid_date`` when it could not be parsed.
    """
    if isinstance(value, datetime):
        return value, None
    if not isinstance(value, str):
        return None, None

    text = value.strip()
    if not text:
        return None, None
    if _DATE_ONLY_PATTERN.match(text):
        date_value = parse_date(text)
        if date_value:
            return datetime.combine(date_value, time.min), "date_only"

    try:
        return isoparse(text), None
    except (ValueError, OverflowError):
        pass

    parsed = parse_datetime(text)
    if parsed:
        return parsed, None
    return None, "invalid_date"


def normalize_country(value: str | None) -> str | None:
    """Return the full English country name for a code or name.

    Event.country is a free-text field, but existing data stores full names,
    so ISO codes such as "DE" are expanded to "Germany" where possible.
    """
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if len(text) == 2:
        country = pycountry.countries.get(alpha_2=text.upper())
        if country:
            return country.name
    try:
        matches = pycountry.countries.search_fuzzy(text)
    except LookupError:
        return text
    if matches:
        return matches[0].name
    return text


def compose_location(venue: str | None, city: str | None) -> str | None:
    """Join venue and city into the single location string the model stores."""
    parts = [part.strip() for part in (venue, city) if part and part.strip()]
    if not parts:
        return None
    if len(parts) == 2 and parts[1].lower() in parts[0].lower():
        parts = parts[:1]
    deduped: list[str] = []
    for part in parts:
        if not deduped or deduped[-1].lower() != part.lower():
            deduped.append(part)
    return ", ".join(deduped)


def absolute_url(base_url: str, candidate: str | None) -> str | None:
    """Resolve a possibly relative URL and reject non-web schemes."""
    if not candidate:
        return None
    text = candidate.strip()
    if not text:
        return None
    if text.startswith("//"):
        text = "https:" + text
    resolved = (
        text if text.startswith(("http://", "https://")) else urljoin(base_url, text)
    )
    return resolved if resolved.startswith(("http://", "https://")) else None


def strip_tracking_params(url: str) -> str:
    """Remove campaign and click-tracking parameters from a URL."""
    parsed = urlsplit(url)
    if not parsed.query:
        return url
    query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_PARAMS
    ]
    return urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment)
    )


def rich_text_to_plain_text(node: object) -> str | None:
    """Flatten a ProseMirror-style rich text document into plain text.

    Luma stores event descriptions as nested JSON nodes; this walks the tree,
    keeps text leaves, and turns block nodes into line breaks.
    """
    if not isinstance(node, (dict, list)):
        return strip_html(node if isinstance(node, str) else None)

    parts: list[str] = []

    def _walk(current: object) -> None:
        if isinstance(current, list):
            for item in current:
                _walk(item)
            return
        if not isinstance(current, dict):
            return
        if current.get("type") == "text" and current.get("text"):
            parts.append(str(current["text"]))
        for child in current.get("content") or []:
            _walk(child)
        if current.get("type") in {"paragraph", "heading", "list_item", "bullet_list"}:
            parts.append("\n")

    _walk(node)
    return strip_html("".join(parts))
