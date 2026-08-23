"""CFP background tasks for email notifications."""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django_tasks import task

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


@task()
def send_cfp_status_notification(submission_id) -> None:
    """Send email notification when CFP status changes.

    Args:
        submission_id: The ID of the CFPSubmission instance (UUID or int).
    """
    from cfps.models import CFPSubmission

    try:
        submission = CFPSubmission.objects.select_related("submitter", "event").get(
            id=submission_id
        )
    except CFPSubmission.DoesNotExist:
        logger.error("CFPSubmission with id %s not found", submission_id)
        return

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


@task()
def send_cfp_skill_match_email(
    speaker_email: str,
    speaker_name: str,
    event_name: str,
    cfp_url: str,
    matched_skills: str,
) -> None:
    """Notify a speaker that a newly published CFP matches their skills."""
    context = {
        "speaker_name": speaker_name,
        "event_name": event_name,
        "cfp_url": cfp_url,
        "matched_skills": matched_skills,
        "site_name": SITE_NAME,
    }
    html = render_to_string("emails/cfp_skill_match.html", context)
    plain_text = render_to_string("emails/cfp_skill_match.txt", context)
    try:
        send_mail(
            subject=f"{SITE_NAME} — New CFP matching your skills: {event_name}",
            message=plain_text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[speaker_email],
            html_message=html,
            fail_silently=False,
        )
        logger.info("CFP skill-match email sent to %s", speaker_email)
    except Exception:
        logger.exception("Failed to send CFP skill-match email to %s", speaker_email)
