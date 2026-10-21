"""Extractor registry, ordered by how precise each source is."""

from events.services.event_import.extract.json_ld import extract as extract_json_ld
from events.services.event_import.extract.microdata import extract as extract_microdata
from events.services.event_import.extract.open_graph import (
    extract as extract_open_graph,
)
from events.services.event_import.extract.platform import extract_platform

EXTRACTORS = (
    extract_platform,
    extract_json_ld,
    extract_microdata,
    extract_open_graph,
)

__all__ = ["EXTRACTORS"]
