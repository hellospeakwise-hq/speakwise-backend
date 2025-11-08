"""attendees serializers."""

from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from attendees.models import Attendance, AttendeeProfile, AttendeeSocialLinks


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


class AttendanceSerializer(serializers.ModelSerializer):
    """attendance serializer."""

    class Meta:
        """meta options."""

        model = Attendance
        fields = ["username", "email", "is_given_feedback"]


class VerifyAttendeeSerializer(serializers.Serializer):
    """verify attendee serializer."""

    email = serializers.EmailField(required=True)
