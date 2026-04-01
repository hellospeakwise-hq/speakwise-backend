"""Speaker request utils."""

from django.conf import settings
from django.core.mail import send_mail
from django_tasks import task
import logging

logger = logging.getLogger(__name__)


@task()
def send_speaker_request_email(
    speaker_email: str, event_name: str, message: str, organizer_name: str = None
) -> None:
    """Send an email notification to the speaker about the speaker request."""
    subject = f"Invitation to Speak at {event_name} – SpeakWise"
    send_mail(
        subject=subject,
        message=message,
        recipient_list=[speaker_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )


@task()
<<<<<<< HEAD
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
    )
=======
def send_request_accepted_email(speaker, _event):
    """Send an email notification to the speaker about the accepted speaker request."""
    subject = f"Speaker Request Accepted for {_event.title}"
    body = (
        f"Hello,\n\n"
        f"Congratulations! Your speaker request for '{_event.title}' "
        f"has been accepted.\n\n"
        f"Best regards,\n"
        f"The SpeakWise Team"
    )
    send_mail(
        subject=subject,
        message=body,
        recipient_list=[speaker.user_account.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )
    # add event and speaker to organization event speakers
    from events.models import EventSpeakers
    EventSpeakers.objects.get_or_create(event=_event, speaker=speaker)
>>>>>>> 9e60841 (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)


@task()
def send_speaker_request_declined_email(speaker, _event):
    """Send an email notification to the speaker about the declined speaker request."""
    subject = f"Speaker Request Declined for {_event.title}"
    body = (
        f"Hello,\n\n"
        f"We regret to inform you that your speaker request for '"
        f"{_event.title}' has been declined.\n\n"
        f"Thank you for your interest.\n\n"
        f"Best regards,\n"
        f"The SpeakWise Team"
    )
<<<<<<< HEAD
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
    )


@task()
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
    )
=======
    send_mail(
        subject=subject,
        message=body,
        recipient_list=[speaker.user_account.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )
>>>>>>> 9e60841 (source /home/ezra/workspace/speakwise-backend/.venv/bin/activate)
