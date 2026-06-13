"""Utility functions for the speakers app."""

import os
import re
import uuid


def sanitize_upload(file):
    """Sanitize an uploaded file's name and return a safe, unique filename.

    Modifies ``file.name`` in-place:
    * Strips path components (prevents path traversal).
    * Replaces special characters with underscores.
    * Collapses consecutive underscores.
    * Preserves the extension in lowercase.
    * Appends a 32-character hex UUID suffix.
    * Leaves file content untouched.
    """
    if not hasattr(file, "name"):
        return file

    stem, ext = os.path.splitext(file.name)
    stem = os.path.basename(stem)
    stem = re.sub(r"[^\w\-.]", "_", stem)
    stem = stem.replace(" ", "_")
    stem = re.sub(r"_+", "_", stem).strip("_")
    ext = ext.lower()

    suffix = uuid.uuid4().hex
    safe_name = f"{stem}_{suffix}{ext}"
    file.name = safe_name

    if hasattr(file, "_name"):
        file._name = safe_name

    return file
