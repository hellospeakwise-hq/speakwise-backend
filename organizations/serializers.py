"""Serializers for the organizations app."""

from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from organizations.choices import OrganizationRole
from organizations.models import Organization, OrganizationMembership
from users.models import User
from users.serializers import UserSerializer


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

    user_detail = UserSerializer(source="user", read_only=True)

    class Meta:
        """Meta class for OrganizationMembershipSerializer."""

        model = OrganizationMembership
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class AddMemberSerializer(ModelSerializer):
    """Serializer for adding a member to an organization."""

    class Meta:
        """Meta class for AddMemberSerializer."""

        model = OrganizationMembership
        fields = ["organization", "user", "role", "added_by"]
        read_only_fields = ["added_by", "created_at", "updated_at"]

    def create(self, validated_data):
        """Add a member to the organization."""
        user = self.context["request"].user
        validated_data["added_by"] = user
        membership = super().create(validated_data)
        return membership

    def validate(self, data):
        """Ensure that the user is not already a member of the organization."""
        organization = data.get("organization")
        user = data.get("user")

        # This won't be needed since DRF already validates the existence
        # with a primary key related field. But kept for clarity.
        if user and not User.objects.filter(id=user.id).exists():
            raise serializers.ValidationError({"user": ["User does not exist."]})

        if (
            organization
            and user
            and OrganizationMembership.objects.filter(
                organization=organization, user=user
            ).exists()
        ):
            raise serializers.ValidationError(
                {"non_field_errors": ["User is already a member of this organization."]}
            )

        return data
