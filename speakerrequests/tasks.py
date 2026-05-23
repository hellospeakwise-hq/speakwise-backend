"""Speaker request utils."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django_tasks import task

logger = logging.getLogger(__name__)


@task()
def send_speaker_request_email(
    recipient_email: str, event_title: str, message: str
) -> None:
    """Send an email notification to the speaker about the speaker request."""
    subject = f"Invitation to Speak at {event_title} – SpeakWise"
    send_mail(
        subject=subject,
        message=message,
        recipient_list=[recipient_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )


@task()
def send_request_accepted_email(recipient_email, event_title):
    """Send an email notification to the speaker about the accepted speaker request."""
    subject = f"Speaker Request Accepted for {event_title}"
    body = (
        f"Hello,\n\n"
        f"Congratulations! Your speaker request for {event_title} "
        f"has been accepted.\n\n"
        f"Best regards,\n"
        f"The SpeakWise Team"
    )
    send_mail(
        subject=subject,
        message=body,
        recipient_list=[recipient_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )


@task()
def send_request_declined_email(recipient_email, event_title):
    """Send an email notification to the speaker about the declined speaker request."""
    subject = f"Speaker Request Declined for {event_title}"
    body = (
        f"Hello,\n\n"
        f"We regret to inform you that your speaker request for '"
        f"{event_title}' has been declined.\n\n"
        f"Thank you for your interest.\n\n"
        f"Best regards,\n"
        f"The SpeakWise Team"
    )
    send_mail(
        subject=subject,
        message=body,
        recipient_list=[recipient_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )


@task()
def send_speaker_deck_upload_email(
    speaker_email: str, event_name: str, upload_url: str
) -> None:
    """Notify an accepted speaker that they can now upload their presentation materials."""
    subject = f"Upload Your Presentation for {event_name}"
    body = (
        f"Hello,\n\n"
        f"Great news! The organizer of '{event_name}' has enabled presentation uploads.\n\n"
        f"Please log in and upload your materials at: {upload_url}\n\n"
        f"Supported formats: PowerPoint (.pptx/.ppt), PDF, Keynote (.key), "
        f"OpenDocument (.odp), or ZIP archives.\n\n"
        f"Best regards,\n"
        f"The {settings.SITE_NAME} Team"
    )
    send_mail(
        subject=subject,
        message=body,
        recipient_list=[speaker_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )
