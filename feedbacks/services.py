"""Business logic for the feedbacks app."""

from django.core.signing import TimestampSigner

from attendees.models import Attendance

signer = TimestampSigner(salt="feedback-verification")


def verify_feedback_token(verify_token: str, max_age: int = 300) -> str:
    """Verify a feedback token and return the attendee's email."""
    signed_data = signer.unsign(verify_token, max_age=max_age)
    return signed_data


def mark_attendance_feedback_given(email: str) -> None:
    """Mark all attendance records for this email as having given feedback."""
    Attendance.objects.filter(email=email, is_given_feedback=False).update(
        is_given_feedback=True
    )
