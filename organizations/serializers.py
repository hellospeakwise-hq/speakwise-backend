"""Serializers for the organizations app."""

from rest_framework import serializers

from organizations.models import Organization, OrganizationMembership


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationMembership."""

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        """Meta options for OrganizationMembershipSerializer."""

        model = OrganizationMembership
        exclude = ["created_at", "updated_at"]
        read_only_fields = [
            "id",
            "username",
            "role",
            "is_active",
            "organization",
            "added_by",
        ]


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for the Organization model."""

    class Meta:
        """Meta class for OrganizationSerializer."""

        model = Organization
        exclude = ["created_at", "updated_at"]
        read_only_fields = ["id", "created_by", "slug", "status", "is_active"]
