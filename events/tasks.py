"""Event background tasks."""

import logging
from uuid import UUID

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django_tasks import task

from events.models import Event
from events.notifications import notify_if_cfp_just_published

logger = logging.getLogger(__name__)

SITE_NAME = getattr(settings, "SITE_NAME", "SpeakWise")


@task()
def notify_if_cfp_just_published_task(event_id: str, was_open: bool):
    """Notify matching speakers when a CFP transitions from closed to open.

    Args:
        event_id: The Event primary key.
        was_open: Whether the CFP was already open before this save.
    """
    try:
        event = Event.objects.get(id=UUID(event_id))
    except Event.DoesNotExist:
        return ("Event with id %s not found", event_id)

    notify_if_cfp_just_published(event, was_open=was_open)


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
        _ = send_mail(
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


def close_expired_cfp_events() -> int:
    """Close CFP submissions for events whose deadline has passed.

    Only events still marked cfp_open are considered; events already closed,
    events without a deadline, and events with a deadline still in the future
    are left untouched. Returns the number of events closed.
    """
    return Event.objects.with_expired_cfp().update(cfp_open=False)


@task()
def close_expired_cfp_events_task() -> int:
    """Background task wrapper for close_expired_cfp_events.

    Intended to run every 24 hours so events with past-deadline CFPs are
    closed even when the event itself has not been saved since the deadline.
    """
    return close_expired_cfp_events()
