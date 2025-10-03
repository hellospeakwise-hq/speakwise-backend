"""speaker request serializers."""

from rest_framework import serializers

from speakerrequests.models import SpeakerRequest


class SpeakerRequestSerializer(serializers.ModelSerializer):
    """speaker request serializer."""

    class Meta:
        """Meta class for speaker request serializer."""

        model = SpeakerRequest
        exclude = ["created_at", "updated_at"]
