"""Organization serializers for user profiles."""

from rest_framework import serializers

from profiles.models.organization_models import OrganizationProfile


class OrganizationProfileSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationProfile model."""

    class Meta:
        """Meta options for OrganizationProfileSerializer."""

        model = OrganizationProfile
        fields = [
            "id",
            "name",
            "description",
            "website",
            "branding",
            "contact_email",
        ]
