"""speaker request serializers."""

from rest_framework import serializers

from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest


class SpeakerRequestSerializer(serializers.ModelSerializer):
    """speaker request serializer."""

    class Meta:
        """Meta class for speaker request serializer."""

        model = SpeakerRequest
        exclude = ["created_at", "updated_at"]


class EmailRequestsSerializer(serializers.ModelSerializer):
    """Email request serializer."""

    class Meta:
        """Meta class for email request serializer."""

        model = SpeakerEmailRequests
        exclude = ["created_at", "updated_at"]

    def validate(self, attrs):
        """Validate email request data."""
        if not attrs.get("request_to", "request_from"):
            raise serializers.ValidationError(
                {"error": "request_to and request_from are required."}
            )
        return attrs
