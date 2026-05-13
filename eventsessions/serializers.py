"""Session serializers."""

from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from eventsessions.models import (
    Session,
    SessionSpeaker,
    SessionSponsor,
    SessionVenue,
    Track,
)


class SessionSpeakerSerializer(serializers.ModelSerializer):
    """Session speaker serializer."""

    class Meta:
        """Metaclass for session speaker serializer."""

        model = SessionSpeaker
        exclude = ["created_at", "updated_at"]


class SessionSponsorSerializer(serializers.ModelSerializer):
    """Session sponsor serializer."""

    class Meta:
        """Metaclass for session sponsor serializer."""

        model = SessionSponsor
        exclude = ["created_at", "updated_at"]


class SessionTrackSerializer(serializers.ModelSerializer):
    """Session track serializer."""

    class Meta:
        """Metaclass for session track serializer."""

        model = Track
        exclude = ["created_at", "updated_at"]


class SessionVenueSerializer(serializers.ModelSerializer):
    """Session venue serializer."""

    class Meta:
        """Metaclass for session venue serializer."""

        model = SessionVenue
        exclude = ["created_at", "updated_at"]


class SessionSerializer(WritableNestedModelSerializer):
    """Session serializer."""

    session_speakers = SessionSpeakerSerializer(many=True, required=False)
    session_sponsors = SessionSponsorSerializer(many=True, required=False)
    track = SessionTrackSerializer(required=False)
    venue = SessionVenueSerializer(required=False)

    class Meta:
        """Metaclass for session serializer."""

        model = Session
        exclude = ["created_at", "updated_at"]
