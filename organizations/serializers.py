"""Serializers for the organizations app."""

from rest_framework import serializers

from organizations.choices import OrganizationRole
from organizations.models import (
    Organization,
    OrganizationMembership,
)


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

    def create(self, validated_data):
        """Create a new organization and add the creator as an admin member."""
        request = self.context.get("request")
        user = request.user if request else None
        validated_data["created_by"] = user
        organization = super().create(validated_data)
        if user:
            OrganizationMembership.objects.create(
                organization=organization,
                user=user,
                role=OrganizationRole.ADMIN,
                added_by=user,
            )
        return organization
