"""talks serializers."""

from rest_framework import serializers

from events.serializers import EventSerializer
from speakers.serializers import SpeakerProfileSerializer
from talks.models import Session, Talks


class SessionSerializer(serializers.ModelSerializer):
    """Session serializer."""

    class Meta:
        """Meta options."""

        model = Session
        exclude = ("created_at", "updated_at", "talk")


class TalkSerializer(serializers.ModelSerializer):
    """Serializer for Talk model."""

    session = SessionSerializer(required=False, many=False)

    class Meta:
        """meta options."""

        model = Talks
        exclude = ("created_at", "updated_at")


class TalkReviewSerializer(serializers.ModelSerializer):
    """Serializer for reviewing talks with detailed speaker and event info."""

    speaker = SpeakerProfileSerializer(read_only=True)
    event = EventSerializer(read_only=True)
    talk_sessions = SessionSerializer(many=True, read_only=True)

    class Meta:
        """meta options."""

        model = Talks
        fields = [
            "id",
            "title",
            "description",
            "speaker",
            "duration",
            "category",
            "presentation_files",
            "event",
            "talk_sessions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
