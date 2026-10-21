"""schema.org Event extraction from HTML microdata."""

from __future__ import annotations

import re
from typing import Any

from events.services.event_import.extract.base import (
    Extraction,
    ExtractionContext,
    ImageCandidate,
)
from events.services.event_import.normalize import (
    compose_location,
    normalize_country,
)

SOURCE = "microdata"
EVENT_ITEMTYPE_PATTERN = re.compile(
    r"(?:^|/)(?:[A-Za-z]*Event|Festival)$", re.IGNORECASE
)


def extract(context: ExtractionContext) -> Extraction:
    """Return Event fields from the first schema.org Event microdata scope."""
    scope = _find_event_scope(context.soup)
    if scope is None:
        return Extraction(source=SOURCE)

    fields: dict[str, Any] = {}
    title = _prop_value(scope, "name")
    if title:
        fields["title"] = title
    description = _prop_value(scope, "description")
    if description:
        fields["description"] = description
    start_date = _prop_value(scope, "startDate")
    if start_date:
        fields["start_date_time"] = start_date
    end_date = _prop_value(scope, "endDate")
    if end_date:
        fields["end_date_time"] = end_date
    website = _prop_value(scope, "url")
    if website:
        fields["website"] = website

    location, country = _location_fields(scope)
    if location:
        fields["location"] = location
    if country:
        fields["country"] = country

    is_free = _offers_is_free(scope)
    if is_free is not None:
        fields["is_free"] = is_free

    image = _prop_value(scope, "image")
    if image:
        fields["event_image_candidates"] = [ImageCandidate(url=image, source=SOURCE)]

    return Extraction(source=SOURCE, fields=fields)


def _find_event_scope(soup):
    """Return the first element whose itemtype is a schema.org Event type."""
    for element in soup.find_all(attrs={"itemtype": True}):
        itemtype = element.get("itemtype")
        if not isinstance(itemtype, str):
            continue
        if EVENT_ITEMTYPE_PATTERN.search(itemtype):
            return element
    return None


def _prop_element(scope, name: str):
    """Return the first element with the requested itemprop."""
    return scope.find(attrs={"itemprop": name})


def _prop_value(scope, name: str) -> str | None:
    """Return the text/content value for an itemprop."""
    element = _prop_element(scope, name)
    if element is None:
        return None
    for attribute in ("content", "datetime", "src", "href"):
        value = element.get(attribute)
        if isinstance(value, str) and value.strip():
            return value.strip()
    text = element.get_text(" ", strip=True)
    return text or None


def _location_fields(scope) -> tuple[str | None, str | None]:
    """Return (location, country) from a microdata location subtree."""
    element = _prop_element(scope, "location")
    if element is None:
        return None, None

    venue = _prop_value(element, "name")
    city = None
    country = None
    address = _prop_element(element, "address")
    if address is not None:
        city = _prop_value(address, "addressLocality") or _prop_value(
            address, "addressRegion"
        )
        country = _prop_value(address, "addressCountry")
    return compose_location(venue, city), normalize_country(country)


def _offers_is_free(scope) -> bool | None:
    """Return whether the microdata offer is marked free."""
    offer = _prop_element(scope, "offers")
    if offer is None:
        return None
    accessible = _prop_value(offer, "isAccessibleForFree")
    if accessible is not None:
        return accessible.lower() == "true"
    price = _prop_value(offer, "price")
    if price is not None:
        try:
            return float(price.replace(",", "")) == 0
        except ValueError:
            return None
    return None
