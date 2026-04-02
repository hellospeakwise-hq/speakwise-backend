"""speaker request serializers."""

from rest_framework import serializers

from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest


class SpeakerRequestSerializer(serializers.ModelSerializer):
    """speaker request serializer."""

    organization_name = serializers.CharField(source="organizer.name", read_only=True)
    speaker_name = serializers.CharField(
        source="speaker.user_account.get_full_name", read_only=True
    )
    event_title = serializers.CharField(source="event.title", read_only=True)

    class Meta:
        """Meta class for speaker request serializer."""

        model = SpeakerRequest
        fields = [
            "id",
            "organization_name",
            "speaker",
            "speaker_name",
            "event",
            "event_title",
            "organizer",
            "status",
            "message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["status", "created_at", "updated_at"]


class EmailRequestsSerializer(serializers.ModelSerializer):
    """Email request serializer."""

    class Meta:
        """Meta class for email request serializer."""

        model = SpeakerEmailRequests
        exclude = ["created_at", "updated_at"]

    def validate(self, attrs):
        """Validate email request data."""
        if not attrs.get("request_to") and not attrs.get("request_from"):
            raise serializers.ValidationError(
                {"error": "request_to and request_from are required."}
            )
        return attrs
