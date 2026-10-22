"""SSRF-safe HTTP fetching for event import.

Every URL a user supplies is resolved and checked before the request is made,
and each redirect target is re-checked. Private, loopback, link-local, and
reserved addresses are rejected so the endpoint cannot be used to probe the
internal network.
"""

from __future__ import annotations

import ipaddress
import socket
import time
from urllib.parse import urljoin, urlsplit

import requests
from django.conf import settings

from events.services.event_import.exceptions import (
    EventFetchError,
    ResponseTooLarge,
    UnsafeImportURL,
    UnsupportedContentType,
)
from events.services.event_import.schemas import FetchedDocument

HTML_CONTENT_TYPES = frozenset({"text/html", "application/xhtml+xml"})
IMAGE_CONTENT_TYPES = frozenset({"image/jpeg", "image/jpg", "image/png", "image/webp"})

BLOCKED_HOSTS = frozenset({"localhost"})
BLOCKED_HOST_SUFFIXES = (
    ".local",
    ".internal",
    ".localhost",
    ".lan",
    ".home.arpa",
)

REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


def _timeout_seconds() -> float:
    """Return the total budget for one outbound request."""
    return float(getattr(settings, "EVENT_IMPORT_REQUEST_TIMEOUT", 10))


def _max_redirects() -> int:
    """Return how many redirect hops are followed."""
    return int(getattr(settings, "EVENT_IMPORT_MAX_REDIRECTS", 3))


def _user_agent() -> str:
    """Return the identifying User-Agent used for outbound fetches."""
    return getattr(
        settings,
        "EVENT_IMPORT_USER_AGENT",
        "SpeakWiseEventImporter/1.0 (+https://speak-wise.live)",
    )


def validate_public_url(url: str) -> str:
    """Return the URL if it is a fetchable public http(s) address.

    Raises UnsafeImportURL for malformed URLs, non-web schemes, credentials,
    non-standard ports, and hostnames that resolve to non-public addresses.
    """
    text = (url or "").strip()
    if not text:
        raise UnsafeImportURL("Enter the URL of an event page.")
    if len(text) > 2048:
        raise UnsafeImportURL("That URL is too long.")

    try:
        parsed = urlsplit(text)
    except ValueError as exc:
        raise UnsafeImportURL("Enter a valid URL.") from exc

    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"}:
        raise UnsafeImportURL("Only http and https URLs are supported.")
    if parsed.username or parsed.password:
        raise UnsafeImportURL("URLs containing credentials are not supported.")

    hostname = (parsed.hostname or "").rstrip(".").lower()
    if not hostname:
        raise UnsafeImportURL("Enter a valid URL.")
    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafeImportURL("Enter a valid URL.") from exc
    if port not in (None, 80, 443):
        raise UnsafeImportURL("Only standard web ports are supported.")
    if hostname in BLOCKED_HOSTS or hostname.endswith(BLOCKED_HOST_SUFFIXES):
        raise UnsafeImportURL("That URL points to a local address.")

    _reject_non_public_addresses(hostname, port or (443 if scheme == "https" else 80))
    return text


def fetch_html(url: str) -> FetchedDocument:
    """Fetch an HTML page with redirect, redirect-target, and size checks."""
    return _fetch(
        url, HTML_CONTENT_TYPES, "EVENT_IMPORT_MAX_HTML_BYTES", 2 * 1024 * 1024
    )


def fetch_image(url: str) -> FetchedDocument:
    """Fetch an image with the same safety checks as fetch_html."""
    return _fetch(
        url, IMAGE_CONTENT_TYPES, "EVENT_IMPORT_MAX_IMAGE_BYTES", 5 * 1024 * 1024
    )


def _fetch(
    url: str,
    allowed_content_types: frozenset[str],
    size_setting: str,
    default_max_bytes: int,
) -> FetchedDocument:
    """Fetch a document, validating every address and redirect target."""
    target = validate_public_url(url)
    max_bytes = int(getattr(settings, size_setting, default_max_bytes))
    deadline = time.monotonic() + _timeout_seconds()
    session = _build_session()

    try:
        for _ in range(_max_redirects() + 1):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise EventFetchError("The event page took too long to respond.")

            response = _get(session, target, remaining)
            try:
                if response.is_redirect or response.status_code in REDIRECT_STATUSES:
                    location = response.headers.get("Location")
                    if not location:
                        raise EventFetchError(
                            "The event page sent an invalid redirect."
                        )
                    target = validate_public_url(urljoin(target, location))
                    continue
                if response.status_code >= 400:
                    raise EventFetchError(
                        f"The event page returned HTTP {response.status_code}."
                    )
                content_type = _content_type(response)
                if content_type and content_type not in allowed_content_types:
                    raise UnsupportedContentType(
                        "The URL does not point to a supported page or image."
                    )
                content = _read_limited(response, max_bytes)
                return FetchedDocument(
                    url=target, content=content, content_type=content_type
                )
            finally:
                response.close()
        raise EventFetchError("The event page redirected too many times.")
    except requests.RequestException as exc:
        raise EventFetchError("Could not reach the event page.") from exc


def _get(session: requests.Session, url: str, remaining: float) -> requests.Response:
    """Issue a single non-redirecting GET within the remaining time budget."""
    connect_timeout = min(5.0, remaining)
    read_timeout = min(10.0, remaining)
    return session.get(
        url,
        stream=True,
        allow_redirects=False,
        timeout=(connect_timeout, read_timeout),
    )


def _build_session() -> requests.Session:
    """Return a session with an identifying User-Agent and no proxy trust."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": _user_agent(),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en",
        }
    )
    # Ignore proxy environment variables so a misconfigured host cannot
    # silently route these outbound fetches through an unintended proxy.
    session.trust_env = False
    return session


def _content_type(response: requests.Response) -> str:
    """Return the lowercased media type, ignoring any charset parameter."""
    return response.headers.get("Content-Type", "").split(";")[0].strip().lower()


def _read_limited(response: requests.Response, max_bytes: int) -> bytes:
    """Read the response body, stopping at the configured byte limit."""
    declared = response.headers.get("Content-Length", "")
    if declared.isdigit() and int(declared) > max_bytes:
        raise ResponseTooLarge("The event page is too large to import.")

    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_content(chunk_size=65536):
        if not chunk:
            continue
        total += len(chunk)
        if total > max_bytes:
            raise ResponseTooLarge("The event page is too large to import.")
        chunks.append(chunk)
    return b"".join(chunks)


def _reject_non_public_addresses(hostname: str, port: int) -> None:
    """Resolve the host and reject any non-public resolved address."""
    try:
        addresses = {
            info[4][0].split("%")[0]
            for info in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        }
    except socket.gaierror as exc:
        raise EventFetchError("Could not resolve the event page host.") from exc

    if not addresses:
        raise EventFetchError("Could not resolve the event page host.")

    for address in addresses:
        try:
            ip = ipaddress.ip_address(address)
        except ValueError as exc:
            raise UnsafeImportURL("Enter a valid URL.") from exc
        if not ip.is_global:
            raise UnsafeImportURL("That URL points to a private or local network.")
