"""events utils."""

from urllib.parse import urlparse


def normalize_event_website(url: str) -> str:
    """Return a comparable form of an event website URL.

    Host is lowercased, a leading ``www.`` is stripped, and a trailing slash
    on the path is removed so equivalent URLs match as duplicates.
    """
    if not url:
        return ""
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parsed.path.rstrip("/").lower()
    return f"{host}{path}"
