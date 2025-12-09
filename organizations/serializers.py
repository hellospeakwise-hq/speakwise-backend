"""Serializers for the organizations app."""

from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import serializers

from organizations.choices import OrganizationRole
from organizations.models import Organization, OrganizationMembership
from users.models import User

user = get_user_model()


class AdditionalMemberInput(serializers.Serializer):
    """Serializer for OrganizationMembershipSerializer."""

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    role = serializers.ChoiceField(
        choices=OrganizationRole.choices, default=OrganizationRole.MEMBER
    )


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationMembership."""

    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        """Meta options for OrganizationMembershipSerializer."""

        model = OrganizationMembership
        exclude = ["added_by", "updated_at"]
        read_only_fields = ["id", "username", "created_at", "updated_at"]


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization."""

    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    members = OrganizationMembershipSerializer(
        source="organization_memberships", many=True, read_only=True
    )

    additional_members = AdditionalMemberInput(
        many=True, write_only=True, required=False
    )

    class Meta:
        """Meta options for OrganizationSerializer."""

        model = Organization
        exclude = ["created_by", "updated_at"]

    def validate(self, attrs):
        """Validate that user and role are authenticated."""
        request = self.context.get("request")
        if (
            not request
            or not getattr(request, "user", None)
            or not request.user.is_authenticated
        ):
            raise serializers.ValidationError(
                {"non_field_errors": ["Authentication required."]}
            )
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        """Serializer creates a new OrganizationMembership."""
        request = self.context.get("request")
        additional_members = validated_data.pop("additional_members", [])

        # Create org with creator
        organization = Organization.objects.create(
            created_by=request.user, **validated_data
        )

        # Build memberships (creator as admin + others as member)
        to_create = [
            OrganizationMembership(
                organization=organization,
                user=request.user,
                role=OrganizationRole.ADMIN,
                added_by=request.user,
                is_active=True,
            )
        ]

        # De-duplicate and avoid adding creator twice
        wanted = {}
        for item in additional_members:
            u = item["user"]
            if u == request.user:
                continue  # don't add creator twice
            wanted[u] = item.get("role", OrganizationRole.MEMBER)

        to_create.extend(
            OrganizationMembership(
                organization=organization,
                user=u,
                role=role,
                added_by=request.user,
                is_active=True,
            )
            for u, role in wanted.items()
        )

        OrganizationMembership.objects.bulk_create(to_create, ignore_conflicts=True)
        return organization

    @transaction.atomic
    def update(self, instance, validated_data):
        """Serializer updates an existing OrganizationMembership."""
        request = self.context.get("request")
        additional_members = validated_data.pop("additional_members", [])

        instance = super().update(instance, validated_data)

        if not additional_members:
            return instance

        # Build desired mapping user->role
        wanted = {}
        for item in additional_members:
            u = item["user"]
            if u == request.user and u == instance.created_by:
                # Optional: prevent downgrading creator here, but we're only adding/upserting
                pass
            wanted[u] = item.get("role", OrganizationRole.MEMBER)

        users = list(wanted.keys())

        # Find existing memberships for these users
        existing_qs = OrganizationMembership.objects.filter(
            organization=instance, user__in=users
        )
        existing_by_user_id = {m.user_id: m for m in existing_qs}

        # Split into new vs existing
        to_create = []
        to_update = []
        for u in users:
            role = wanted[u]
            m = existing_by_user_id.get(u.id)
            if m is None:
                to_create.append(
                    OrganizationMembership(
                        organization=instance,
                        user=u,
                        role=role,
                        added_by=request.user,
                        is_active=True,
                    )
                )
            else:
                if m.role != role:
                    m.role = role
                    to_update.append(m)

        if to_create:
            OrganizationMembership.objects.bulk_create(to_create, ignore_conflicts=True)
        if to_update:
            OrganizationMembership.objects.bulk_update(
                to_update, ["role"]
            )  # Django >= 2.2

        return instance
