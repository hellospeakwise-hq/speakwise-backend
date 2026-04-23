"""Speaker request utils."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django_tasks import task

<<<<<<< HEAD
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
=======
FRONTEND_URL = getattr(settings, "FRONTEND_URL", "https://speak-wise.live")


def _send(subject: str, plain_text: str, html: str, recipient: str) -> None:
    send_mail(
        subject=subject,
        message=plain_text,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        html_message=html,
        fail_silently=False,
    )


@task()
def send_speaker_org_request_email(
    speaker_email: str,
    speaker_name: str,
    organization_name: str,
    organizer_name: str,
    event_name: str,
    event_date: str,
    message: str,
    request_id: int,
) -> None:
    """Notify a speaker that an organisation has sent them an official request."""
    html = render_to_string(
        "emails/speaker_org_request_received.html",
        {
            "speaker_name": speaker_name,
            "organization_name": organization_name,
            "organizer_name": organizer_name,
            "event_name": event_name,
            "event_date": event_date,
            "message": message,
            "request_id": request_id,
        },
    )
    _send(
        subject=f"{organization_name} has invited you to speak at {event_name}",
        plain_text=(
            f"Hi {speaker_name},\n\n"
            f"{organization_name} has sent you a speaking invitation for {event_name}.\n\n"
            f"Message: {message}\n\n"
            f"View request: {FRONTEND_URL}/dashboard/speaker?tab=requests&highlight={request_id}"
        ),
        html=html,
        recipient=speaker_email,
>>>>>>> 39bd44e (Add welcome email templates for organizers and speakers)
    )


@task()
<<<<<<< HEAD
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
=======
def send_speaker_email_request_email(
    speaker_email: str,
    speaker_name: str,
    requester_name: str,
    requester_email: str,
    event_name: str,
    event_location: str,
    message: str,
    request_id: str,
) -> None:
    """Notify a speaker that someone sent them a direct (non-org) speaking request."""
    html = render_to_string(
        "emails/speaker_email_request_received.html",
        {
            "speaker_name": speaker_name,
            "requester_name": requester_name,
            "requester_email": requester_email,
            "event_name": event_name,
            "event_location": event_location,
            "message": message,
            "request_id": request_id,
        },
    )
    _send(
        subject=f"{requester_name} wants you to speak at {event_name}",
        plain_text=(
            f"Hi {speaker_name},\n\n"
            f"{requester_name} ({requester_email}) has sent you a speaking request for {event_name}.\n\n"
            f"Message: {message}\n\n"
            f"View request: {FRONTEND_URL}/dashboard/speaker?tab=requests&highlight={request_id}"
        ),
        html=html,
        recipient=speaker_email,
>>>>>>> 39bd44e (Add welcome email templates for organizers and speakers)
    )


@task()
<<<<<<< HEAD
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
=======
def send_request_accepted_email(
    organizer_email: str,
    requester_name: str,
    speaker_name: str,
    speaker_title: str,
    event_name: str,
    event_date: str,
    event_location: str,
    speaker_profile_url: str,
    dashboard_url: str,
) -> None:
    """Notify the organiser that the speaker accepted their request."""
    html = render_to_string(
        "emails/request_accepted.html",
        {
            "requester_name": requester_name,
            "speaker_name": speaker_name,
            "speaker_title": speaker_title,
            "event_name": event_name,
            "event_date": event_date,
            "event_location": event_location,
            "speaker_profile_url": speaker_profile_url,
            "dashboard_url": dashboard_url,
        },
    )
    _send(
        subject=f"{speaker_name} accepted your speaking request for {event_name}",
        plain_text=(
            f"Hi {requester_name},\n\n"
            f"Great news! {speaker_name} has accepted your speaking request for {event_name}.\n\n"
            f"Go to your dashboard: {dashboard_url}"
        ),
        html=html,
        recipient=organizer_email,
    )


@task()
def send_request_declined_email(
    organizer_email: str,
    requester_name: str,
    speaker_name: str,
    event_name: str,
    discover_url: str,
) -> None:
    """Notify the organiser that the speaker declined their request."""
    html = render_to_string(
        "emails/request_rejected.html",
        {
            "requester_name": requester_name,
            "speaker_name": speaker_name,
            "event_name": event_name,
            "discover_url": discover_url,
        },
    )
    _send(
        subject=f"{speaker_name} is unavailable for {event_name}",
        plain_text=(
            f"Hi {requester_name},\n\n"
            f"{speaker_name} has declined your speaking request for {event_name}.\n\n"
            f"Find another speaker: {discover_url}"
        ),
        html=html,
        recipient=organizer_email,
>>>>>>> 39bd44e (Add welcome email templates for organizers and speakers)
    )
