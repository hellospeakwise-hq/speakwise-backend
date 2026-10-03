"""Shared file-upload validators.

All user-supplied images and files funnel through these validators so no
endpoint accepts arbitrary extensions or unbounded payloads. Limits are
deliberately conservative: avatars/blog/event images stay small, while
presentation decks allow a larger budget.
"""

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]
PRESENTATION_EXTENSIONS = ["pdf", "ppt", "pptx", "jpg", "jpeg", "png", "webp"]

MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024
MAX_PRESENTATION_SIZE_BYTES = 20 * 1024 * 1024

validate_image_extension = FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS)
validate_presentation_extension = FileExtensionValidator(
    allowed_extensions=PRESENTATION_EXTENSIONS
)


def validate_image_size(value):
    """Reject images larger than MAX_IMAGE_SIZE_BYTES."""
    if value and getattr(value, "size", 0) > MAX_IMAGE_SIZE_BYTES:
        raise ValidationError(
            f"Image file too large (max {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)}MB)."
        )


def validate_presentation_size(value):
    """Reject presentation files larger than MAX_PRESENTATION_SIZE_BYTES."""
    if value and getattr(value, "size", 0) > MAX_PRESENTATION_SIZE_BYTES:
        raise ValidationError(
            f"File too large (max {MAX_PRESENTATION_SIZE_BYTES // (1024 * 1024)}MB)."
        )
