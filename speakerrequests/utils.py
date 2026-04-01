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
    send_mail(
        subject=subject,
        message=body,
        recipient_list=[speaker.user_account.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )