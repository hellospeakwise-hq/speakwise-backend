"""Business logic for the attendees app."""

from django.core.signing import TimestampSigner

from attendees.models import Attendance

signer = TimestampSigner(salt="feedback-verification")


def verify_attendee_email(email: str) -> dict:
    """Verify an attendee by email and return verification data.

    Args:
        email: The attendee's email address.

    Returns:
        dict with 'email', 'verify_token', and 'detail'.

    Raises:
        Attendance.DoesNotExist: If no attendance record exists for this email.
        ValueError: If the attendee has already given feedback.
    """
    attendances = Attendance.objects.filter(email=email)
    if not attendances.exists():
        raise Attendance.DoesNotExist("Attendee not found")

    if attendances.filter(is_given_feedback=True).exists():
        raise ValueError("Attendee already given feedback")

    verify_token = signer.sign(email)

    return {
        "email": email,
        "verify_token": verify_token,
        "detail": "Attendee verified. You may now submit feedback.",
    }
