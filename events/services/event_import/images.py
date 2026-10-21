"""Event image selection, signed tokens, and validated downloads.

The preview only returns a signed token. The image itself is downloaded and
re-encoded when the user submits the event, which keeps arbitrary remote URLs
out of the create endpoint.
"""

from __future__ import annotations

import io

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.signing import BadSignature, SignatureExpired, dumps, loads
from PIL import Image, UnidentifiedImageError

from events.services.event_import.exceptions import ImageImportError
from events.services.event_import.extract.base import ImageCandidate
from events.services.event_import.fetcher import fetch_image

IMAGE_TOKEN_SALT = "events.event-import.image-token"
IMAGE_TOKEN_MAX_AGE_SECONDS = 30 * 60
MAX_IMAGE_PIXELS = 40_000_000

_FORMAT_EXTENSIONS = {
    "JPEG": "jpg",
    "PNG": "png",
    "WEBP": "webp",
}


def select_image_candidate(
    candidates: list[ImageCandidate],
) -> ImageCandidate | None:
    """Return the best image candidate, preferring the largest resolution.

    Candidates arrive in source-priority order, and Python's stable sort keeps
    that order when dimensions are equal or unknown.
    """
    usable = [
        candidate
        for candidate in candidates
        if candidate.url.startswith(("http://", "https://"))
        and len(candidate.url) <= 2048
    ]
    if not usable:
        return None
    return sorted(
        usable,
        key=lambda candidate: (candidate.width or 0) * (candidate.height or 0),
        reverse=True,
    )[0]


def sign_image_token(url: str, user_id: object) -> str:
    """Return a signed, expiring token carrying the image URL and owner."""
    return dumps(
        {"url": url, "user_id": str(user_id)},
        salt=IMAGE_TOKEN_SALT,
        compress=True,
    )


def resolve_image_token(token: str, user_id: object) -> str:
    """Return the image URL if the token is valid, unexpired, and owned by user."""
    max_age = int(
        getattr(
            settings, "EVENT_IMPORT_IMAGE_TOKEN_MAX_AGE", IMAGE_TOKEN_MAX_AGE_SECONDS
        )
    )
    try:
        payload = loads(token, salt=IMAGE_TOKEN_SALT, max_age=max_age)
    except SignatureExpired as exc:
        raise ImageImportError(
            "The imported image link has expired. Upload an image instead."
        ) from exc
    except BadSignature as exc:
        raise ImageImportError("The imported image link is not valid.") from exc

    if str(payload.get("user_id")) != str(user_id):
        raise ImageImportError("The imported image link is not valid.")
    url = payload.get("url")
    if not isinstance(url, str) or not url.startswith(("http://", "https://")):
        raise ImageImportError("The imported image link is not valid.")
    return url


def download_import_image(token: str, user_id: object) -> ContentFile:
    """Fetch, validate, and re-encode the image behind a signed token."""
    url = resolve_image_token(token, user_id)
    document = fetch_image(url)
    data, extension = _sanitize_image(document.content)
    return ContentFile(data, name=f"event-import.{extension}")


def _sanitize_image(data: bytes) -> tuple[bytes, str]:
    """Verify the bytes are a still JPEG/PNG/WebP image and strip metadata."""
    try:
        with Image.open(io.BytesIO(data)) as image:
            image_format = (image.format or "").upper()
            if image_format not in _FORMAT_EXTENSIONS:
                raise ImageImportError(
                    "Only JPEG, PNG, and WebP event images are supported."
                )
            if getattr(image, "n_frames", 1) > 1:
                raise ImageImportError("Animated event images are not supported.")
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise ImageImportError("The event image is too large to process.")
            image.load()
            if image_format == "JPEG" and image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")
            buffer = io.BytesIO()
            save_options = {"optimize": True} if image_format != "WEBP" else {}
            image.save(buffer, format=image_format, **save_options)
    except UnidentifiedImageError as exc:
        raise ImageImportError("The event image could not be read.") from exc
    except (OSError, ValueError, Image.DecompressionBombError) as exc:
        raise ImageImportError("The event image could not be read.") from exc

    return buffer.getvalue(), _FORMAT_EXTENSIONS[image_format]
