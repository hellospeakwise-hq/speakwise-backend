"""speaker request utils."""

from organizers.models import OrganizerProfile
from speakers.models import SpeakerProfile


def speaker_request_payload(organizer_user, speaker_id, data):
    """Generate speaker request payload."""
    payload = {
        "speaker": SpeakerProfile.objects.get(pk=data.get("speaker")),
        "organizer": OrganizerProfile.objects.get(user_account=organizer_user),
        "event": data.get("event"),
        "message": data.get("message"),
        "status": data.get("status"),
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
    }
    return payload
