"""CFP email notification service."""

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)

SITE_NAME = getattr(settings, "SITE_NAME", "SpeakWise")

_MESSAGES = {
    "accepted": (
        "Congratulations! Your CFP submission has been accepted.",
        lambda submission: (
            f"Hi {submission.submitter.first_name or submission.submitter.username},\n\n"
            f"Great news! Your talk submission for {submission.event.title} has been accepted.\n\n"
            f"Talk: {submission.elevator_pitch}\n\n"
            f"The organising team will be in touch with next steps.\n\n"
            f"— The {SITE_NAME} Team"
        ),
    ),
    "rejected": (
        "Update on your CFP submission.",
        lambda submission: (
            f"Hi {submission.submitter.first_name or submission.submitter.username},\n\n"
            f"Thank you for submitting to {submission.event.title}. "
            f"After careful review, we are unable to accept your talk this time.\n\n"
            f"We hope to see you at the event and encourage you to submit again in the future.\n\n"
            f"— The {SITE_NAME} Team"
        ),
    ),
}


class CFPEmailService:
    """Service for sending CFP status notification emails."""

    @staticmethod
    def send_status_notification(submission):
        """Send an email to the submitter when their CFP status changes."""
        entry = _MESSAGES.get(submission.status)
        if not entry:
            return

        subject_suffix, body_fn = entry
        subject = f"{SITE_NAME} — {subject_suffix}"
        message = body_fn(submission)

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[submission.submitter.email],
                fail_silently=False,
            )
            logger.info(
                "CFP status email sent to %s (status=%s)",
                submission.submitter.email,
                submission.status,
            )
        except Exception as e:
            logger.error(
                "Failed to send CFP status email to %s: %s",
                submission.submitter.email,
                e,
            )
