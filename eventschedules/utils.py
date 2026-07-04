"""Event schedule utils."""

from eventsessions.models import Session


def create_event_schedule_payload(event) -> dict:
    """Create an event schedule from payload."""
    schedule_sessions = []
    try:
        sessions = Session.objects.filter(event=event.id)
        if sessions.count() == 0:
            raise ValueError(f"No sessions found for event {event.id}")

        for session in sessions:
            schedule_sessions.append(session.id)

        return {
            "event": event.id,
            "sessions": schedule_sessions,
        }
    except Session.DoesNotExist as error:
        raise ValueError(str(error)) from error
