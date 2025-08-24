"""Organizer serializers."""

from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

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
