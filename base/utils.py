"""organizers services file."""

import os
import re
import tempfile

import pandas
from django.db import transaction
from email_validator import EmailNotValidError, validate_email

from attendees.models import Attendance


class FileHandler:
    """file handler class."""

    def __str__(self):
        """Return string representation of file."""
        return (
            "Handle the extraction of emails from uploaded csv/excel attendance list."
        )

    def _save_extracted_attendee_profile(self, email_list, name_list, event):
        """Save extracted emails, save unto a database."""
        if event is None:
            raise ValueError("Event is required.")

        normalized_pairs = []
        for email, name in zip(email_list, name_list, strict=False):
            try:
                v = validate_email(email, check_deliverability=True, strict=True)
                normalized_email = v.normalized  # canonical form
            except EmailNotValidError as err:
                raise ValueError("Email is not valid: ", str(email)) from err
            normalized_pairs.append((normalized_email, name or ""))

        if not normalized_pairs:
            return Attendance.objects.filter(event=event)

        first_name_by_email = {}
        for e, n in normalized_pairs:
            if e not in first_name_by_email:
                first_name_by_email[e] = n

        emails = list(first_name_by_email.keys())

        existing = set(
            Attendance.objects.filter(event=event, email__in=emails).values_list(
                "email", flat=True
            )
        )

        to_create = [
            Attendance(email=e, event=event, username=first_name_by_email[e])
            for e in emails
            if e not in existing
        ]

        if to_create:
            with transaction.atomic():
                Attendance.objects.bulk_create(to_create, batch_size=1000)

        return Attendance.objects.filter(event=event)

    def _extract_attendee_profiles(self, uploaded_file, event=None):
        """Extract emails from csv or excel file."""
        if not os.path.exists(uploaded_file) or not os.path.isfile(uploaded_file):
            raise ValueError("File does not exist.")

        if not uploaded_file.endswith(".csv") and not uploaded_file.endswith(".xlsx"):
            raise ValueError("File is not a csv or excel file.")

        # Load with pandas
        data_frame = (
            pandas.read_csv(uploaded_file)
            if uploaded_file.endswith(".csv")
            else pandas.read_excel(uploaded_file)
        )

        # Normalize headers: lowercase, collapse non-alphanum to spaces, strip
        def norm(s: str) -> str:
            return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()

        normalized_map = {norm(c): c for c in data_frame.columns}

        # Candidate header variants
        email_candidates = {
            "email",
            "emails",
            "email address",
            "e mail",
            "e mail address",
            "e mail addresses",
        }
        name_candidates = {"name", "full name", "username", "attendee name"}

        # Find best email column
        email_col = None
        for key, original in normalized_map.items():
            if key in email_candidates or key.split(" ")[-1] == "email":
                email_col = original
                break
        if not email_col:
            # fallback: any column containing 'email'
            for key, original in normalized_map.items():
                if "email" in key:
                    email_col = original
                    break
        if not email_col:
            raise ValueError("Could not find an email column.")

        # Find optional name column
        name_col = None
        for key, original in normalized_map.items():
            if key in name_candidates:
                name_col = original
                break
        if not name_col:
            # fallback common patterns
            for key, original in normalized_map.items():
                if "name" in key:
                    name_col = original
                    break

        _email_list = data_frame[email_col].dropna().astype(str).tolist()
        if name_col:
            # Align lengths; fill with empty strings if needed
            _name_series = data_frame[name_col].fillna("").astype(str)
            _name_list = _name_series.tolist()
        else:
            _name_list = [""] * len(_email_list)
        return self._save_extracted_attendee_profile(
            _email_list, _name_list, event=event
        )

    def clean_file(self, file_obj, event=None):
        """Validate and persist an uploaded CSV/Excel file to a temp path."""
        if not file_obj:
            raise FileNotFoundError("No file provided.")

        allowed_exts = {".csv", ".xlsx"}
        allowed_ct = {
            "text/csv",
            "application/csv",
            "text/plain",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        max_bytes = 20 * 1024 * 1024  # 20 MB

        filename = getattr(file_obj, "name", "")
        ext = os.path.splitext(filename)[1].lower()

        if ext not in allowed_exts:
            raise ValueError("Only .csv or .xlsx files are allowed.")

        content_type = getattr(file_obj, "content_type", None)
        if content_type and content_type not in allowed_ct:
            raise ValueError("Unsupported content type.")

        size = getattr(file_obj, "size", None)
        if size is not None and size > max_bytes:
            raise ValueError("File too large.")

        written = 0
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_file:
                for chunk in file_obj.chunks():
                    written += len(chunk)
                    if written > max_bytes:
                        raise ValueError("File too large.")
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
        except Exception:
            try:
                if "temp_file_path" in locals() and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
            except FileNotFoundError as err:
                raise ValueError("file does not exist.") from err
            raise

        return self._extract_attendee_profiles(temp_file_path, event=event)
