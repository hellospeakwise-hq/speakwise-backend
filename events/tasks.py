"""Event background tasks."""

from django_tasks import task

from events.models import Event


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
