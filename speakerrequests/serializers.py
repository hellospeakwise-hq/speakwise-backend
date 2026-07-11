"""speaker request serializers."""

from rest_framework import serializers

from speakerrequests.choices import RequestStatusChoices
from speakerrequests.models import SpeakerEmailRequests, SpeakerRequest


class SpeakerRequestSerializer(serializers.ModelSerializer):
    """speaker request serializer."""

    class Meta:
        """Meta class for speaker request serializer."""

        model = SpeakerRequest
        exclude = ["created_at", "updated_at"]


class SpeakerRequestUpdateSerializer(serializers.ModelSerializer):
    """speaker request serializer."""

    class Meta:
        """Meta class for speaker request serializer."""

        model = SpeakerRequest
        exclude = ["created_at", "updated_at", "status"]


class OrganizationSpeakerRequestCancelSerializer(serializers.ModelSerializer):
    """speaker request serializer."""

    class Meta:
        """Meta class for speaker request serializer."""

        model = SpeakerRequest
        fields = ["status", "response_message"]

    def update(self, instance, validated_data):
        """Update speaker request status."""
        instance.cancel(response_message=validated_data.get("response_message"))
        return instance


class SpeakerRequestAcceptDeclineSerializer(serializers.ModelSerializer):
    """speaker request serializer."""

    class Meta:
        """Meta class for speaker request accept/decline serializer."""

        model = SpeakerRequest
        fields = ["status", "response_message"]

    def update(self, instance, validated_data):
        """Update speaker request status."""
        if validated_data.get("status") == RequestStatusChoices.ACCEPTED:
            instance.accept(response_message=validated_data.get("response_message"))
        elif validated_data.get("status") == RequestStatusChoices.DECLINED:
            instance.decline(response_message=validated_data.get("response_message"))
        return instance


class EmailSpeakerRequestsSerializer(serializers.ModelSerializer):
    """Email request serializer."""

    class Meta:
        """Meta class for email request serializer."""

        model = SpeakerEmailRequests
        exclude = ["created_at", "updated_at"]

    def validate(self, attrs):
        """Validate email request data."""
        if not attrs.get("request_to") or not attrs.get("request_from"):
            raise serializers.ValidationError(
                {"error": "request_to and request_from are required."}
            )
        return attrs
