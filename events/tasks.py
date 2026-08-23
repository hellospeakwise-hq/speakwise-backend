"""Event background tasks."""

import logging

from django_tasks import task

logger = logging.getLogger(__name__)


@task()
def notify_if_cfp_just_published_task(event_id, was_open: bool) -> None:
    """Notify matching speakers when a CFP transitions from closed to open.

    Args:
        event_id: The Event primary key.
        was_open: Whether the CFP was already open before this save.
    """
    from events.models import Event
    from events.notifications import notify_if_cfp_just_published

    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        logger.error("Event with id %s not found", event_id)
        return

    notify_if_cfp_just_published(event, was_open=was_open)
