"""Exceptions raised while importing an event from an external page."""

from rest_framework.exceptions import APIException


class EventImportError(Exception):
    """Base class for event import failures."""


class UnsafeImportURL(EventImportError):
    """The supplied URL is not a public http(s) address we may fetch."""


class EventFetchError(EventImportError):
    """The external page could not be fetched."""


class UnsupportedContentType(EventFetchError):
    """The external response is not an HTML page or a supported image."""


class ResponseTooLarge(EventFetchError):
    """The external response exceeds the configured size limit."""


class ImageImportError(EventImportError):
    """An imported image token is invalid or its image cannot be used."""


class EventImportUnavailable(APIException):
    """Upstream event page could not be fetched or returned an error."""

    status_code = 502
    default_detail = (
        "Could not fetch the event page. Try again or enter the details manually."
    )
    default_code = "event_import_unavailable"
