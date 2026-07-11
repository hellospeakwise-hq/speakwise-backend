"""Event schedule utils."""

from uuid import UUID

from eventsessions.models import Session


def create_event_schedule_payload(event: UUID) -> dict:
    """Create an event schedule from payload."""
    schedule_sessions = []
    sessions = Session.objects.filter(event=event)
    if sessions.count() == 0:
        raise ValueError(f"No sessions found for event {event}")

    for session in sessions:
        schedule_sessions.append(session.id)

    return {
        "event": event,
        "sessions": schedule_sessions,
    }
