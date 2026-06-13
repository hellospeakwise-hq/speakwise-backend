"""speaker request tasks."""

from django.template.loader import render_to_string
from django_tasks import task

from base.constants import FRONTEND_URL, SITE_NAME
from base.email import send_email


@task()
def send_speaker_org_request_email(
    event_name: str,
    speaker_name: str,
    organization_name: str,
    organizer_name: str,
    message: str,
    request_id: str,
    recipient_email: str,
) -> None:
    """Notify a speaker that an organisation has sent them an official request."""
    html = render_to_string(
        "emails/speaker_org_request_received.html",
        {
            "speaker_name": speaker_name,
            "organization_name": organization_name,
            "organizer_name": organizer_name,
            "event_name": event_name,
            "event_date": "",
            "message": message,
            "request_id": request_id,
        },
    )
    send_email(
        subject=f"{organization_name} has invited you to speak at {event_name}",
        plain_body=(
            f"Hi {speaker_name},\n\n"
            f"{organization_name} has sent you a speaking invitation for {event_name}.\n\n"
            f"Message: {message}\n\n"
            f"View request: {FRONTEND_URL}/dashboard/speaker?tab=requests&highlight={request_id}"
        ),
        html_body=html,
        recipient=recipient_email,
    )


@task()
def send_speaker_email_request_email(
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
    send_email(
        subject=f"{requester_name} wants you to speak at {event_name}",
        plain_body=(
            f"Hi {speaker_name},\n\n"
            f"{requester_name} ({requester_email}) has sent you a speaking request for {event_name}.\n\n"
            f"Message: {message}\n\n"
            f"View request: {FRONTEND_URL}/dashboard/speaker?tab=requests&highlight={request_id}"
        ),
        html_body=html,
        recipient=requester_email,
    )


@task()
def send_request_accepted_email(
    speaker_name, requester_name, requester_email, event_name
) -> None:
    """Notify the organiser that the speaker accepted their request."""
    dashboard_url = f"{FRONTEND_URL}/dashboard/organizer"

    html = render_to_string(
        "emails/request_accepted.html",
        {
            "requester_name": requester_name,
            "speaker_name": speaker_name,
            "speaker_title": "",
            "event_name": event_name,
            "event_date": "",
            "event_location": "",
            "speaker_profile_url": "",
            "dashboard_url": dashboard_url,
        },
    )
    send_email(
        subject=f"{speaker_name} accepted your speaking request for {event_name}",
        plain_body=(
            f"Hi {requester_name},\n\n"
            f"Great news! {speaker_name} has accepted your speaking request for {event_name}.\n\n"
            f"Go to your dashboard: {dashboard_url}"
        ),
        html_body=html,
        recipient=str(requester_email),
    )


@task()
def send_request_declined_email(
    speaker_name, requester_name, requester_email, event_name
) -> None:
    """Notify the organiser that the speaker declined their request."""
    discover_url = f"{FRONTEND_URL}/discover"

    html = render_to_string(
        "emails/request_rejected.html",
        {
            "requester_name": requester_name,
            "speaker_name": speaker_name,
            "event_name": event_name,
            "discover_url": discover_url,
        },
    )
    send_email(
        subject=f"{speaker_name} is unavailable for {event_name}",
        plain_body=(
            f"Hi {requester_name},\n\n"
            f"{speaker_name} has declined your speaking request for {event_name}.\n\n"
            f"Find another speaker: {discover_url}"
        ),
        html_body=html,
        recipient=str(requester_email),
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
        f"The {SITE_NAME} Team"
    )
    send_email(
        subject=subject,
        plain_body=body,
        html_body=None,
        recipient=speaker_email,
    )
