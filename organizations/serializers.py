"""Serializers for the organizations app."""

from rest_framework import serializers

from organizations.choices import OrganizationRole
from organizations.models import Organization, OrganizationMembership
from users.models import User


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationMembership."""

    user_id = serializers.IntegerField(write_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        """meta options."""

        model = OrganizationMembership
        fields = ["id", "user_id", "username", "role", "is_active", "created_at"]
        read_only_fields = ["id", "username", "created_at"]


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for the Organization model."""

    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    members = OrganizationMembershipSerializer(
        source="organization_memberships", many=True, read_only=True
    )
    additional_members = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="User IDs to add as members (creator is auto-added as admin)",
    )

    class Meta:
        """Meta class for OrganizationSerializer."""

        model = Organization
        exclude = ["created_at", "updated_at"]
        read_only_fields = [
            "id",
            "created_by_username",
            "members",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Create a new organization."""
        request = self.context.get("request")
        additional_members = validated_data.pop("additional_members", [])
        validated_data["created_by"] = request.user
        organization = Organization.objects.create(**validated_data)

        OrganizationMembership.objects.create(
            organization=organization,
            user=request.user,
            role=OrganizationRole.ADMIN,
            added_by=request.user,
            is_active=True,
        )

        for user_id in additional_members:
            try:
                user = User.objects.get(id=user_id)
                OrganizationMembership.objects.create(
                    organization=organization,
                    user=user,
                    role=OrganizationRole.MEMBER,
                    added_by=request.user,
                    is_active=True,
                )
            except User.DoesNotExist:
                pass

        return organization

    def update(self, instance, validated_data):
        """Update an organization."""
        request = self.context.get("request")
        additional_members = validated_data.pop("additional_members", [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for user_id in additional_members:
            try:
                user = User.objects.get(id=user_id)
                OrganizationMembership.objects.get_or_create(
                    organization=instance,
                    user=user,
                    defaults={
                        "role": OrganizationRole.MEMBER,
                        "added_by": request.user,
                        "is_active": True,
                    },
                )
            except User.DoesNotExist:
                pass

        return instance
