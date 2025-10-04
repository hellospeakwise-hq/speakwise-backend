"""Organization serializers."""

from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

from users.serializers import UserSerializer

from .models import Organization, OrganizationMembership, OrganizationRole


class OrganizationMembershipSerializer(serializers.ModelSerializer):
    """Serializer for organization membership."""

    class Meta:
        """Meta class for OrganizationMembershipSerializer."""

        model = OrganizationMembership
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class OrganizationSerializer(WritableNestedModelSerializer):
    """Serializer for Organization with nested memberships."""

    memberships = OrganizationMembershipSerializer(
        source="organization_memberships", many=True, read_only=True
    )
    created_by = UserSerializer(read_only=True)
    admin_count = serializers.SerializerMethodField()
    member_count = serializers.SerializerMethodField()

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
            "is_active",
            "created_by",
            "memberships",
            "admin_count",
            "member_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def validate_name(self, value):
        """Validate organization name uniqueness."""
        # Remove extra whitespace and convert to title case for consistency
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "Organization name must be at least 2 characters long."
            )

        # Check for global uniqueness (case-insensitive)
        existing_org = Organization.objects.filter(name__iexact=value)

        # If this is an update, exclude the current instance
        if self.instance:
            existing_org = existing_org.exclude(id=self.instance.id)

        if existing_org.exists():
            existing_name = existing_org.first().name
            raise serializers.ValidationError(
                f"An organization with the name '{existing_name}' already exists. "
                f"Please choose a different name."
            )

        return value

    def validate_email(self, value):
        """Validate organization email uniqueness."""
        if not value:
            return value

        # Check for global uniqueness
        existing_org = Organization.objects.filter(email__iexact=value)

        # If this is an update, exclude the current instance
        if self.instance:
            existing_org = existing_org.exclude(id=self.instance.id)

        if existing_org.exists():
            raise serializers.ValidationError(
                "An organization with this email already exists."
            )

        return value.lower()  # Store emails in lowercase for consistency

    def get_admin_count(self, obj):
        """Get count of admin members."""
        return obj.organization_memberships.filter(
            role=OrganizationRole.ADMIN, is_active=True
        ).count()

    def get_member_count(self, obj):
        """Get count of all active members."""
        return obj.organization_memberships.filter(is_active=True).count()

    def create(self, validated_data):
        """Create organization and make creator an admin."""
        user = self.context["request"].user
        validated_data["created_by"] = user

        organization = super().create(validated_data)

        # Create admin membership for creator
        OrganizationMembership.objects.create(
            organization=organization,
            user=user,
            role=OrganizationRole.ADMIN,
            added_by=user,
        )

        return organization


class AddOrganizerSerializer(serializers.Serializer):
    """Serializer for adding organizers to an organization."""

    user_id = serializers.IntegerField()
    role = serializers.ChoiceField(
        choices=OrganizationRole.choices, default=OrganizationRole.ORGANIZER
    )
    can_review_talks = serializers.BooleanField(default=True)
    can_manage_events = serializers.BooleanField(default=False)
    can_add_organizers = serializers.BooleanField(default=False)

    def validate_user_id(self, value):
        """Validate that user exists."""
        from users.models import User

        if not User.objects.filter(id=value).exists():
            raise serializers.ValidationError("User not found.")
        return value

    def validate(self, data):
        """Validate role and permissions."""
        if data["role"] == OrganizationRole.ADMIN:
            # Admins automatically get all permissions
            data["can_manage_events"] = True
            data["can_add_organizers"] = True

        return data
