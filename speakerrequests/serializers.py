"""speaker request serializers."""

from speakerrequests.models import SpeakerRequest
from rest_framework import serializers


class SpeakerRequestSerializer(serializers.ModelSerializer):
    """speaker request serializer."""
    class Meta:
        model = SpeakerRequest
        exclude = ["created_at", "updated_at"]
