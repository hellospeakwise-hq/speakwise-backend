"""events utils."""


def create_event_payload(request):
    """Create event payload."""
    payload = request.data.copy()
    return payload
