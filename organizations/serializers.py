"""Serializers for the organizations app."""

from rest_framework import serializers

from organizations.models import Organization, OrganizationMembership


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationMembership."""

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        """Meta options for OrganizationMembershipSerializer."""

        model = OrganizationMembership
        fields = [
            "id",
            "organization",
            "user",
            "username",
            "role",
            "is_active",
            "added_by",
        ]
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
        fields = [
            "id",
            "name",
            "description",
            "email",
            "website",
            "logo",
            "status",
            "is_active",
            "created_by",
            "slug",
        ]
        read_only_fields = ["id", "created_by", "slug", "status", "is_active"]
