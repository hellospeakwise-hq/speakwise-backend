import os
import re
import uuid

from django.core.files.uploadedfile import UploadedFile


def sanitize_upload(file: UploadedFile) -> UploadedFile:
    """Sanitize an uploaded file by cleaning its filename.

    Strips path traversal components, replaces non-alphanumeric characters
    (except dots and hyphens), and renames the file to a UUID-based name to
    prevent filename collisions and enumeration.
    """
    original_name = os.path.basename(file.name)
    _, ext = os.path.splitext(original_name)
    ext = ext.lower()

    safe_stem = re.sub(r"[^\w\-]", "_", os.path.splitext(original_name)[0])
    safe_stem = re.sub(r"_+", "_", safe_stem).strip("_")

    file.name = f"{safe_stem}_{uuid.uuid4().hex}{ext}"
    return file
