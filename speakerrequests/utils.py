"""speaker request utils."""

from django.conf import settings
from django.core.mail import send_mail
from django_tasks import task

from events.models import EventSpeakers


@task()
def send_speaker_request_email(
    speaker_email: str, event_name: str, message: str, organizer_name: str = None
) -> None:
    """Send an email notification to the speaker about the speaker request."""
    subject = f"Invitation to Speak at {event_name} – We’d Love to Feature You"
    send_mail(
        subject=subject,
        message=message,
        recipient_list=[speaker_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )

@task()
def create_event_speaker(speaker, event):
    """Create an event speaker."""
    from events.models import EventSpeakers
    
    try:
        EventSpeakers.objects.create(event=event, speaker=speaker)
    except Exception as err:
        raise Exception(err) from err

@task()
def send_request_accepted_email(speaker, _event):
    """Send an email notification to the speaker about the accepted speaker request."""
    subject = f"Your Speaker Request for {_event.name} has been Accepted"
    body = (
        f"Hello,\n\n"
        f"Congratulations! Your speaker request for the event '{_event.name}' "
        f"has been accepted.\n\n"
        f"Please log in to your account for more details.\n\n"
        f"Best regards,\n"
        f"The SpeakWise Team"
    )
    send_mail(
        subject=subject,
        message=body,
        recipient_list=[speaker.email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )
    # add event and speaker to organization event speakers
    create_event_speaker.enqueue(speaker=speaker, event=_event)


@task()
def send_speaker_request_declined_email(speaker, _event):
    """Send an email notification to the speaker about the declined speaker request."""    
    subject = f"Your Speaker Request for {_event.name} has been Declined"
    body = (
        f"Hello,\n\n"
        f"We regret to inform you that your speaker request for the event '"
        f"{_event.name}' has been declined.\n\n"
        f"Thank you for your interest, and we encourage you to apply for future events.\n\n"
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