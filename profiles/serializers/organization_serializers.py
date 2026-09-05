"""Organization serializers for user profiles."""

from rest_framework import serializers

from profiles.models.organization_models import OrganizationCFP, OrganizationProfile


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
            "cfps",
        ]
        read_only_fields = ["owner", "status", "id"]
