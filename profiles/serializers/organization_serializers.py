"""Organization serializers for user profiles."""

from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from profiles.models.organization_models import OrganizationCFP, OrganizationProfile
from profiles.services.organization_services import (
    get_organization_limit,
    has_reached_organization_limit,
    lock_organization_owner,
)


class OrganizationCFPSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationCFP model."""

    class Meta:
        """Meta-options for OrganizationCFPSerializer."""

        model = OrganizationCFP
        fields = ["url", "description", "open_at", "close_at"]


class OrganizationProfileSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationProfile model."""

    cfps = OrganizationCFPSerializer(read_only=True, required=False)

    class Meta:
        """Meta-options for OrganizationProfileSerializer."""

        model = OrganizationProfile
        fields = [
            "id",
            "owner",
            "name",
            "description",
            "website",
            "branding",
            "contact_email",
            "status",
            "admin_notes",
            "cfps",
        ]
        read_only_fields = ["owner", "status", "admin_notes", "id"]

    @transaction.atomic
    def create(self, validated_data):
        """Create an organization profile owned by the requesting user.

        Speakers may own organizations too. A user can own up to their
        organization limit (see ``get_organization_limit``); the owner row is
        locked first so concurrent requests cannot exceed it. The owner is
        always the requesting user — it can never be supplied by the client.
        """
        request = self.context.get("request")
        if not (request and request.user.is_authenticated):
            raise ValidationError(
                {"detail": "Must be authenticated to create a profile."}
            )

        user = request.user
        lock_organization_owner(user)
        if has_reached_organization_limit(user):
            limit = get_organization_limit(user)
            raise ValidationError(
                {
                    "detail": "You have reached the maximum number of "
                    f"organizations you can own ({limit})."
                }
            )

        validated_data["owner"] = user
        return super().create(validated_data)
