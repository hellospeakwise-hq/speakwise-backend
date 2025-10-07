"""speaker request utils."""

from django.conf import settings
from django.core.mail import send_mail


def send_speaker_request_email(speaker_email, event_name, organizer_name, message):
    """Send an email notification to the speaker about the speaker request."""
    subject = f"Speaker Request for {event_name}"
    body = (
        f"Hello,\n\n"
        f"You have received a speaker request from {organizer_name} for the event '{event_name}'.\n\n"
        f"Message:\n{message}\n\n"
        f"Please log in to your account to respond to this request.\n\n"
        f"Best regards,\n"
        f"The SpeakWise Team"
    )
    send_mail(
        subject=subject,
        message=body,
        recipient_list=[speaker_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )


def send_request_accepted_email(speaker_email, event_name, speaker_name):
    """Send an email notification to the speaker about the accepted speaker request."""
    subject = f"Your Speaker Request for {event_name} has been Accepted"
    body = (
        f"Hello,\n\n"
        f"Congratulations! Your speaker request for the event '{event_name}' has been accepted by {speaker_name}.\n\n"
        f"Please log in to your account for more details.\n\n"
        f"Best regards,\n"
        f"The SpeakWise Team"
    )
    send_mail(
        subject=subject,
        message=body,
        recipient_list=[speaker_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )


def send_speaker_request_declined_email(speaker_email, event_name, speaker_name):
    """Send an email notification to the speaker about the declined speaker request."""
    subject = f"Your Speaker Request for {event_name} has been Declined"
    body = (
        f"Hello,\n\n"
        f"We regret to inform you that your speaker request for the event '{event_name}' has been declined by {speaker_name}.\n\n"
        f"Thank you for your interest, and we encourage you to apply for future events.\n\n"
        f"Best regards,\n"
        f"The SpeakWise Team"
    )
    send_mail(
        subject=subject,
        message=body,
        recipient_list=[speaker_email],
        from_email=settings.DEFAULT_FROM_EMAIL,
        fail_silently=False,
    )
