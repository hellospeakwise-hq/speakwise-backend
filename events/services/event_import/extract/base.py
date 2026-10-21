"""Shared extractor contracts."""

import json
from dataclasses import dataclass, field
from typing import Any

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class ImageCandidate:
    """A potential event image, with optional dimensions for selection."""

    url: str
    source: str
    width: int | None = None
    height: int | None = None


@dataclass
class Extraction:
    """Fields discovered by a single extractor.

    ``fields`` uses canonical Event field names; ``event_image_candidates`` is
    internal and carries every candidate image found by the extractor.
    """

    source: str
    fields: dict[str, Any] = field(default_factory=dict)
    warnings: list[dict[str, str]] = field(default_factory=list)


@dataclass(frozen=True)
class ExtractionContext:
    """The parsed page shared by every extractor."""

    url: str
    soup: BeautifulSoup


def warning(code: str, message: str) -> dict[str, str]:
    """Build a stable warning payload for the API response."""
    return {"code": code, "message": message}


def next_data(soup: BeautifulSoup) -> dict:
    """Return the parsed Next.js __NEXT_DATA__ payload, or an empty dict.

    Luma, Devfolio, and KonfHub render with Next.js and embed the server
    payload in a JSON script tag. It is the most reliable source when the
    page itself exposes no schema.org data.
    """
    script = soup.find("script", id="__NEXT_DATA__")
    if script is None:
        return {}
    raw = (script.string or script.get_text() or "").strip()
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}
