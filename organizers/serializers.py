"""Organizer serializers."""

from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from attendees.models import Attendance

from .models import OrganizerProfile, OrganizerSocialLinks


class OrganizerSocialLinksSerializer(serializers.ModelSerializer):
    """Serializer for organizer social links."""

    class Meta:
        """Meta options."""

        model = OrganizerSocialLinks
        exclude = ["created_at", "updated_at", "organizer"]


class OrganizerProfileSerializer(WritableNestedModelSerializer):
    """Serializer for organizer profiles with nested social links."""

    social_links = OrganizerSocialLinksSerializer(many=True, required=False)

    class Meta:
        """Meta options."""

        model = OrganizerProfile
        exclude = ["created_at", "updated_at"]


class AttendanceSerializer(serializers.ModelSerializer):
    """file upload serializer."""

    class Meta:
        """meta options."""

        model = Attendance
        fields = ["id", "username", "email", "event", "is_given_feedback"]


class FileUploadSerializer(serializers.Serializer):
    """file upload serializer."""

    file = serializers.FileField()
    event = serializers.IntegerField(required=True)
