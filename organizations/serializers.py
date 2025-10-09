"""Serializers for the organizations app."""

from rest_framework.serializers import ModelSerializer

from organizations.choices import OrganizationRole
from organizations.models import Organization, OrganizationMembership


class OrganizationSerializer(ModelSerializer):
    """Serializer for the Organization model."""

    class Meta:
        """Meta class for OrganizationSerializer."""

        model = Organization
        fields = "__all__"
        read_only_fields = ["created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        """Create an organization and assign the creator as an admin."""
        user = self.context["request"].user
        validated_data["created_by"] = user
        organization = super().create(validated_data)
        OrganizationMembership.objects.create(
            organization=organization,
            user=user,
            role=OrganizationRole.ADMIN,
            added_by=user,
        )
        return organization


class OrganizationMembershipSerializer(ModelSerializer):
    """Serializer for the OrganizationMembership model."""

    class Meta:
        """Meta class for OrganizationMembershipSerializer."""

        model = OrganizationMembership
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]
