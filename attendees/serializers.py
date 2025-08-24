"""attendees serializers."""

from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from attendees.models import AttendeeProfile, AttendeeSocialLinks


class AttendeeSocialLinksSerializer(serializers.ModelSerializer):
    """attendee social links serializer."""

    class Meta:
        """meta options."""

        model = AttendeeSocialLinks
        exclude = ["created_at", "updated_at", "attendee"]


class AttendeeProfileSerializer(WritableNestedModelSerializer):
    """attendee serializer."""

    social_links = AttendeeSocialLinksSerializer(many=True, read_only=True)

    class Meta:
        """meta options."""

        model = AttendeeProfile
        exclude = ["created_at", "updated_at"]
