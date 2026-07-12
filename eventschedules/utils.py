"""Event schedule utils."""

from uuid import UUID

from eventsessions.models import Session


def create_event_schedule_payload(event_id: UUID) -> dict:
    """Create an event schedule from payload."""
    schedule_sessions = []
    sessions = Session.objects.filter(event=event_id)
    if sessions.count() == 0:
        raise ValueError(f"No sessions found for event {event_id}")

    for session in sessions:
        schedule_sessions.append(session.id)

    return dict(event=event_id, sessions=schedule_sessions)
